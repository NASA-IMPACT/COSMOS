# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_workflow_status_triggers.py

from unittest.mock import Mock, patch

import pytest
from django.db import transaction
from django.test import TestCase, TransactionTestCase

from sde_collections.models.collection import Collection, WorkflowHistory
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.delta_url import DumpUrl
from sde_collections.tasks import (
    fetch_full_text,
    migrate_dump_to_delta_and_handle_status_transistions,
)
from sde_collections.tests.factories import CollectionFactory, DumpUrlFactory


class TestWorkflowStatusTransitions(TestCase):
    """P5 trigger table: the dispatcher (handle_workflow_status_change) drives only the
    crawl4ai/indexing pipeline — every Sinequa branch is gone."""

    def setUp(self):
        self.collection = CollectionFactory()

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_ready_for_engineering_triggers_scrape_dispatch(self, mock_dispatch):
        """When status changes to READY_FOR_ENGINEERING, it should dispatch a scrape job (P3:
        replaces the Sinequa create_scraper_config/create_scraper_job trigger)."""
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        mock_dispatch.assert_called_once_with(self.collection.id)

    @patch("sde_collections.tasks.fetch_full_text.delay")
    def test_indexing_finished_triggers_nothing(self, mock_fetch):
        """INDEXING_FINISHED_ON_DEV is a Sinequa-era status: its full-text-fetch trigger is
        gone (the P4 ingest replaces the fetch entirely)."""
        self.collection.workflow_status = WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV
        self.collection.save()

        mock_fetch.assert_not_called()

    @patch("sde_collections.models.collection.Collection.create_indexer_config")
    @patch("sde_collections.models.collection.Collection.create_indexer_job")
    def test_ready_for_curation_triggers_nothing(self, mock_indexer_job, mock_indexer_config):
        """The Sinequa indexer-config branch on READY_FOR_CURATION is gone."""
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        self.collection.save()

        mock_indexer_config.assert_not_called()
        mock_indexer_job.assert_not_called()

    @patch("sde_collections.tasks.index_collection_to_test.delay")
    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_curated_promotes_and_enqueues_test_indexing(self, mock_promote, mock_index_test):
        """CURATED promotes DeltaUrls to CuratedUrls AND hands off to test indexing."""
        self.collection.workflow_status = WorkflowStatusChoices.CURATED
        self.collection.save()

        mock_promote.assert_called_once()
        mock_index_test.assert_called_once_with(self.collection.id)

    @patch("sde_collections.models.collection.Collection.add_to_public_query")
    @patch("sde_collections.tasks.index_collection_to_prod.delay")
    def test_quality_check_statuses_enqueue_prod_indexing(self, mock_index_prod, mock_add):
        """QC_PERFECT / QC_MINOR hand off to prod indexing; add_to_public_query is gone."""
        for status in [WorkflowStatusChoices.QUALITY_CHECK_PERFECT, WorkflowStatusChoices.QUALITY_CHECK_MINOR]:
            collection = CollectionFactory()
            collection.workflow_status = status
            collection.save()

            mock_index_prod.assert_called_with(collection.id)
        assert mock_index_prod.call_count == 2
        mock_add.assert_not_called()

    @patch("sde_collections.tasks.index_collection_to_test.delay")
    def test_reentrancy_guard_prevents_recursion(self, mock_index_test):
        """A save() performed inside a trigger must not re-fire the dispatcher."""

        def promote_and_save_again():
            # Simulates a trigger mutating and saving the same instance.
            self.collection.save()

        with patch(
            "sde_collections.models.collection.Collection.promote_to_curated",
            side_effect=promote_and_save_again,
        ) as mock_promote:
            self.collection.workflow_status = WorkflowStatusChoices.CURATED
            self.collection.save()

        mock_promote.assert_called_once()
        mock_index_test.assert_called_once()


class TestSlackNotificationOnTransition(TestCase):
    """P5: the Slack send moved out of Collection.save() into the post_save receiver."""

    def setUp(self):
        self.collection = CollectionFactory(workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS)

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    @patch("sde_collections.models.collection.send_slack_message")
    def test_mapped_transition_sends_message_once(self, mock_send, mock_dispatch):
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        mock_send.assert_called_once()
        assert self.collection.name in mock_send.call_args.args[0] or "<" in mock_send.call_args.args[0]

    @patch("sde_collections.models.collection.send_slack_message")
    def test_unmapped_transition_sends_nothing(self, mock_send):
        self.collection.workflow_status = WorkflowStatusChoices.MERGE_PENDING
        self.collection.save()

        mock_send.assert_not_called()

    @patch("sde_collections.models.collection.send_slack_message", side_effect=Exception("slack down"))
    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_slack_failure_does_not_break_the_save(self, mock_dispatch, mock_send):
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()  # must not raise

        self.collection.refresh_from_db()
        assert self.collection.workflow_status == WorkflowStatusChoices.READY_FOR_ENGINEERING


class TestReindexingStatusTransitions(TestCase):
    def setUp(self):
        self.collection = CollectionFactory(
            workflow_status=WorkflowStatusChoices.PROD_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NOT_NEEDED,
        )

    @patch("sde_collections.tasks.fetch_full_text.delay")
    def test_reindexing_finished_triggers_nothing(self, mock_fetch):
        """REINDEXING_FINISHED_ON_DEV must trigger nothing: the P4 ingest sets this status
        itself — a fetch trigger here would double-fire."""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
        self.collection.save()

        mock_fetch.assert_not_called()

    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_reindexing_curated_triggers_promotion(self, mock_promote):
        """When reindexing status changes to CURATED, it should promote DeltaUrls"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_CURATED
        self.collection.save()

        mock_promote.assert_called_once()


class TestFullTextImport(TestCase):
    def setUp(self):
        self.collection = CollectionFactory()
        self.existing_dump = DumpUrlFactory(collection=self.collection)
        self.api_response = [
            {"url": "http://example.com/1", "title": "Title 1", "full_text": "Content 1"},
            {"url": "http://example.com/2", "title": "Title 2", "full_text": "Content 2"},
        ]

    @patch("sde_collections.utils.slack_utils.send_detailed_import_notification")
    @patch("sde_collections.tasks.Api")
    @patch("sde_collections.models.collection.GitHubHandler")
    def test_full_text_import_workflow(self, MockGitHub, MockApi, MockSlackNotification):
        """Test the full process of importing full text data"""
        # Setup mock GitHub handler with proper XML content
        mock_github = Mock()
        mock_github.check_file_exists.return_value = True
        mock_file_contents = Mock()
        # Include all the fields that convert_template_to_plugin_indexer checks for
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Sinequa>
            <connector>crawler2</connector>
            <description></description>
            <identity></identity>
            <indexers></indexers>
            <index></index>
            <domain></domain>
            <treeRoot></treeRoot>
            <Revision>1</Revision>
            <visibility></visibility>
            <ForceReindexation>false</ForceReindexation>
            <Url></Url>
            <Plugin>SMD_Plugins/Sinequa.Plugin.WebCrawler_Index_URLList</Plugin>
            <WorkerCount>3</WorkerCount>
            <MaxWorkerPerHost></MaxWorkerPerHost>
            <UrlList></UrlList>
            <DynamicUrlList></DynamicUrlList>
            <IncludedExtensions></IncludedExtensions>
            <ExcludedExtensions></ExcludedExtensions>
            <IncludedFilenames></IncludedFilenames>
            <ExcludedFilenames></ExcludedFilenames>
            <IncludedFolders></IncludedFolders>
            <ExcludedFolders></ExcludedFolders>
            <EnableNeuralIndexing>true</EnableNeuralIndexing>
            <NeuralSearchSelectionQuery></NeuralSearchSelectionQuery>
            <UrlStayInside>true</UrlStayInside>
            <MaxLevel></MaxLevel>
            <MaxToIndex></MaxToIndex>
            <MaxToCrawl></MaxToCrawl>
            <MaxRedirection></MaxRedirection>
            <CrawlMaxSize></CrawlMaxSize>
            <CrawlTimeout></CrawlTimeout>
            <NormalizeUrls>true</NormalizeUrls>
            <CorrectDomainCookies>false</CorrectDomainCookies>
            <IgnoreSessionCookies>false</IgnoreSessionCookies>
            <DownloadImages>true</DownloadImages>
            <DownloadMedia>true</DownloadMedia>
            <DownloadCss>false</DownloadCss>
            <DownloadFtp>true</DownloadFtp>
            <DownloadFile>true</DownloadFile>
            <IndexJs>false</IndexJs>
            <FollowJs>true</FollowJs>
            <CrawlFlash>true</CrawlFlash>
            <IndexEmptyPages>true</IndexEmptyPages>
            <CrawlWebsphereSeedlist>true</CrawlWebsphereSeedlist>
            <KeepHashFragmentInUrl>false</KeepHashFragmentInUrl>
            <RetryCount></RetryCount>
            <RetryPause></RetryPause>
            <HttpCodesToRetry></HttpCodesToRetry>
            <UseIfModifiedSince>true</UseIfModifiedSince>
            <UseIfNoneMatch>no</UseIfNoneMatch>
            <AcceptWeakETag>false</AcceptWeakETag>
            <ForcedEncoding></ForcedEncoding>
            <UseCompression>false</UseCompression>
            <UseUnsafeHeaderParsing>false</UseUnsafeHeaderParsing>
            <NormalizeSecureSchemesWhenTestingVisited>false</NormalizeSecureSchemesWhenTestingVisited>
            <ExactDeduplication>false</ExactDeduplication>
            <NearDeduplication>false</NearDeduplication>
            <CrawlPauseDelay></CrawlPauseDelay>
            <CrawlPauseCount></CrawlPauseCount>
            <UseRuntimeAutoRedirect>false</UseRuntimeAutoRedirect>
            <RememberDnsFailure>true</RememberDnsFailure>
            <RememberConnectFailure>true</RememberConnectFailure>
            <RememberTrustFailure>true</RememberTrustFailure>
            <RememberProxyNameResolutionFailure>false</RememberProxyNameResolutionFailure>
            <UseRobotsNoIndex>false</UseRobotsNoIndex>
            <UseRobotsNoFollow>true</UseRobotsNoFollow>
            <UseRobotsTxt>false</UseRobotsTxt>
            <RobotsTxtCaseSensitive>false</RobotsTxtCaseSensitive>
            <LoadRobotsTxtSitemapUrls>false</LoadRobotsTxtSitemapUrls>
            <CheckSitemapUrlLastmodInRealtimeMode>false</CheckSitemapUrlLastmodInRealtimeMode>
            <AddRobotsTxtAllowUrlsToSeedList>false</AddRobotsTxtAllowUrlsToSeedList>
            <UseCanonicalLinks>false</UseCanonicalLinks>
            <UseRelNoFollow>false</UseRelNoFollow>
            <DownloadSelectionQuery></DownloadSelectionQuery>
            <FollowSelectionQuery></FollowSelectionQuery>
            <IndexSelectionQuery></IndexSelectionQuery>
            <LoadDefaultTags>true</LoadDefaultTags>
            <LoadDefaultJsTransforms>true</LoadDefaultJsTransforms>
            <UrlAccess>
                <UseDefaultCredentials>true</UseDefaultCredentials>
                <UseDefaultNetworkCredentials>false</UseDefaultNetworkCredentials>
                <User></User>
                <Password></Password>
                <Domain></Domain>
                <UseRfc1945>false</UseRfc1945>
                <Timeout></Timeout>
                <ChangeConnectionGroupNameOnTimeout>false</ChangeConnectionGroupNameOnTimeout>
                <AllowAuthenticatedConnectionSharing>true</AllowAuthenticatedConnectionSharing>
                <PreAuthenticate>false</PreAuthenticate>
                <HttpVersion></HttpVersion>
                <KeepAlive>true</KeepAlive>
                <SecurityProtocol></SecurityProtocol>
                <UserAgent></UserAgent>
                <ClientCertificateFile></ClientCertificateFile>
                <ClientCertificatePassword></ClientCertificatePassword>
                <ClientCertificateStorage></ClientCertificateStorage>
                <AllowXPathCookies>false</AllowXPathCookies>
                <UseHttpClientForWebRequests>false</UseHttpClientForWebRequests>
                <ThrottleManagerCode>expBackoff+headers</ThrottleManagerCode>
                <UseBrowserForWebRequests>false</UseBrowserForWebRequests>
                <BrowserForWebRequestsReadinessThreshold></BrowserForWebRequestsReadinessThreshold>
                <BrowserForWebRequestsInitialDelay></BrowserForWebRequestsInitialDelay>
                <BrowserForWebRequestsMaxTotalDelay></BrowserForWebRequestsMaxTotalDelay>
                <BrowserForWebRequestsMaxResourcesDelay></BrowserForWebRequestsMaxResourcesDelay>
                <BrowserForWebRequestsLogLevel></BrowserForWebRequestsLogLevel>
                <BrowserForWebRequestsViewportWidth></BrowserForWebRequestsViewportWidth>
                <BrowserForWebRequestsViewportHeight></BrowserForWebRequestsViewportHeight>
                <BrowserForWebRequestsAdditionalJavascript></BrowserForWebRequestsAdditionalJavascript>
                <WebConnectionPluginName></WebConnectionPluginName>
                <PostLoginUrl></PostLoginUrl>
                <PostLoginData></PostLoginData>
                <GetBeforePostLogin>false</GetBeforePostLogin>
                <PostLoginAutoRedirect>true</PostLoginAutoRedirect>
                <ReLoginCount></ReLoginCount>
                <ReLoginDelay></ReLoginDelay>
                <DetectHtmlLoginPattern></DetectHtmlLoginPattern>
                <BrowserLogin>
                    <Activate>false</Activate>
                    <RemoteDebuggingPort></RemoteDebuggingPort>
                    <BrowserLogLevel></BrowserLogLevel>
                    <ShowDevTools>false</ShowDevTools>
                    <SuccessCondition></SuccessCondition>
                    <CookieFilter></CookieFilter>
                </BrowserLogin>
                <FtpUser></FtpUser>
                <FtpPassword></FtpPassword>
                <FtpDomain></FtpDomain>
                <FtpUseBinary>true</FtpUseBinary>
                <FtpUsePassive>true</FtpUsePassive>
                <FtpReadWriteTimeout></FtpReadWriteTimeout>
                <FtpTimeout></FtpTimeout>
                <FtpEnableSsl>false</FtpEnableSsl>
                <FileUser></FileUser>
                <FilePassword></FilePassword>
                <FileDomain></FileDomain>
                <FileTimeout></FileTimeout>
                <AmazonS3>
                    <AccessKey></AccessKey>
                    <SecretKey></SecretKey>
                    <RegionEndpoint>eu-west-1</RegionEndpoint>
                    <ServiceURL></ServiceURL>
                </AmazonS3>
                <ProxyAutoDetect>true</ProxyAutoDetect>
                <ProxyAddress></ProxyAddress>
                <ProxyBypassOnLocal>true</ProxyBypassOnLocal>
                <ProxyServer></ProxyServer>
                <ProxyPort></ProxyPort>
                <ProxyUseDefaultCredentials>true</ProxyUseDefaultCredentials>
                <ProxyUseDefaultNetworkCredentials>false</ProxyUseDefaultNetworkCredentials>
                <ProxyUser></ProxyUser>
                <ProxyPassword></ProxyPassword>
                <ProxyDomain></ProxyDomain>
            </UrlAccess>
            <System>
                <LogLevel>INFO</LogLevel>
            </System>
            <DisplayLongProperties>false</DisplayLongProperties>
            <LongPropertyLimit></LongPropertyLimit>
            <UsePerformanceMetrics>true</UsePerformanceMetrics>
            <LogPerformanceMetricsPeriodically>false</LogPerformanceMetricsPeriodically>
            <LogPerformanceMetricsPeriod></LogPerformanceMetricsPeriod>
            <PasswordRepository></PasswordRepository>
            <StoreDocumentCache></StoreDocumentCache>
            <AuditEnabled>false</AuditEnabled>
            <SaveDeniedDocs>false</SaveDeniedDocs>
            <SavePropertiesToRegistry>false</SavePropertiesToRegistry>
            <CollectionStateNative>false</CollectionStateNative>
            <HtmlNavigatorNative>true</HtmlNavigatorNative>
            <XPathNavigatorNative>false</XPathNavigatorNative>
            <StatusMaxOk></StatusMaxOk>
            <DelApiSecret></DelApiSecret>
            <IndexerClient>
                <Simulate>false</Simulate>
                <SimulateGetCollectionState>false</SimulateGetCollectionState>
                <QueueMaxCount></QueueMaxCount>
                <SendingThreadFactor></SendingThreadFactor>
                <DirectFileAccess>false</DirectFileAccess>
                <UseCompression>false</UseCompression>
                <SessionIsFinishedWait>false</SessionIsFinishedWait>
                <SendTimeout></SendTimeout>
                <RetryConnectCount></RetryConnectCount>
                <RetryConnectDelay></RetryConnectDelay>
                <RetryTimeout></RetryTimeout>
                <RetrySleep></RetrySleep>
                <DeactivationTimeout></DeactivationTimeout>
            </IndexerClient>
            <Indexation>
                <SimulateLemma>false</SimulateLemma>
                <SimulateEngine>false</SimulateEngine>
                <SimulateCache>false</SimulateCache>
                <SimulateLemmaMin></SimulateLemmaMin>
                <SimulateLemmaMax></SimulateLemmaMax>
                <CollectionStateParallelRowFetch></CollectionStateParallelRowFetch>
                <EngineMetaEnabled>true</EngineMetaEnabled>
                <ThumbnailHeight></ThumbnailHeight>
                <ThumbnailWidth></ThumbnailWidth>
                <ThumbnailSmallTimeout></ThumbnailSmallTimeout>
                <ThumbnailMediumTimeout></ThumbnailMediumTimeout>
                <ThumbnailLargeTimeout></ThumbnailLargeTimeout>
                <SynchThumbnailGen>false</SynchThumbnailGen>
                <StoreInCollectionCache>false</StoreInCollectionCache>
                <GetFilePropertiesFromConverter>false</GetFilePropertiesFromConverter>
            </Indexation>
            <CollectDocumentProperties>true</CollectDocumentProperties>
            <DocCountLimitOnCollectProperties></DocCountLimitOnCollectProperties>
            <ForceBlobSend>false</ForceBlobSend>
            <ContinueOnError>true</ContinueOnError>
            <DoDelete>true</DoDelete>
            <DeleteOnError>false</DeleteOnError>
            <DeleteOnNetworkOrServerError>false</DeleteOnNetworkOrServerError>
            <DeleteOnEnumerationError>false</DeleteOnEnumerationError>
            <AcceptDeleteAll>false</AcceptDeleteAll>
            <DeleteMaxPercentThreshold></DeleteMaxPercentThreshold>
            <DeleteMaxThreshold></DeleteMaxThreshold>
            <DeleteMinRemainingThreshold></DeleteMinRemainingThreshold>
            <SaveCollectionState>false</SaveCollectionState>
            <IncrementalState>false</IncrementalState>
            <RealTimeIncrementalState>true</RealTimeIncrementalState>
            <RealTimeInfoOnError>false</RealTimeInfoOnError>
            <ConversionProxies></ConversionProxies>
            <ConversionPlan></ConversionPlan>
            <AddBaseHref>true</AddBaseHref>
            <AddMetaContentType>false</AddMetaContentType>
            <Throttle></Throttle>
            <DocumentClass></DocumentClass>
            <ConnectorLanguage></ConnectorLanguage>
            <ClearHttpRequestCanonicalizeAsFilePath>true</ClearHttpRequestCanonicalizeAsFilePath>
            <PdfGen>
                <ConverterType></ConverterType>
                <TimeoutSmall></TimeoutSmall>
                <TimeoutMedium></TimeoutMedium>
                <TimeoutLarge></TimeoutLarge>
            </PdfGen>
            <IndexZipContent>false</IndexZipContent>
            <IndexPdfAttachments>false</IndexPdfAttachments>
            <IndexOleAttachments>false</IndexOleAttachments>
            <IndexMsgContent>false</IndexMsgContent>
            <IndexMsgAttachments>false</IndexMsgAttachments>
            <IndexOftContent>false</IndexOftContent>
            <IndexOftAttachments>false</IndexOftAttachments>
            <IndexEmlContent>false</IndexEmlContent>
            <IndexEmlAttachments>false</IndexEmlAttachments>
            <IndexPstContent>false</IndexPstContent>
            <IndexOstContent>false</IndexOstContent>
            <IndexPstMsg>true</IndexPstMsg>
            <IndexPstMsgAttachments>true</IndexPstMsgAttachments>
            <IndexPstContact>false</IndexPstContact>
            <IndexPstCalendar>false</IndexPstCalendar>
            <IndexPstNote>false</IndexPstNote>
            <IndexPstTask>false</IndexPstTask>
            <IndexPstDocument>true</IndexPstDocument>
            <PstUseSafeId>false</PstUseSafeId>
            <IndexArchivesExtensions></IndexArchivesExtensions>
            <ArchiveItemsUseArchiveVersion>false</ArchiveItemsUseArchiveVersion>
            <UseShortAttachmentId>false</UseShortAttachmentId>
            <UseExtendedExtensionGuesser>false</UseExtendedExtensionGuesser>
            <AlwaysScanContainerFiles>false</AlwaysScanContainerFiles>
            <XmpExtensions></XmpExtensions>
            <MediaExtensions></MediaExtensions>
            <ExiftoolExtensions></ExiftoolExtensions>
            <EarlySelectionQuery></EarlySelectionQuery>
            <SelectionQuery></SelectionQuery>
            <AttachmentSelectionQuery></AttachmentSelectionQuery>
            <ArchiveItemSelectionQuery></ArchiveItemSelectionQuery>
            <EngineConnectionWait></EngineConnectionWait>
            <FetchCollectionDataDirectlyFromEngine></FetchCollectionDataDirectlyFromEngine>
            <CalculateGraphBoost>false</CalculateGraphBoost>
            <GraphBoostColumn></GraphBoostColumn>
            <GraphBoostEMColumn></GraphBoostEMColumn>
            <GraphBoostIterations></GraphBoostIterations>
            <GraphBoostPower></GraphBoostPower>
            <GraphBoostAdd></GraphBoostAdd>
            <UseFieldPermissions>false</UseFieldPermissions>
            <ShardIndexes></ShardIndexes>
            <ShardingStrategy></ShardingStrategy>
            <ShardSelections></ShardSelections>
            <CurationType></CurationType>
            <CurationIdPattern></CurationIdPattern>
            <RunIndexMiningInIndexer>false</RunIndexMiningInIndexer>
            <Namespace></Namespace>
            <Mapping>
                <Name>id</Name>
                <Value>doc.url1</Value>
            </Mapping>
            <UrlRefererStayInside>false</UrlRefererStayInside>
            <FollowLinks>false</FollowLinks>
        </Sinequa>"""
        mock_file_contents.decoded_content = mock_xml.encode("utf-8")
        mock_github._get_file_contents.return_value = mock_file_contents
        MockGitHub.return_value = mock_github

        # Setup mock API
        mock_api = Mock()
        mock_api.get_full_texts.return_value = iter([self.api_response])
        MockApi.return_value = mock_api

        # Setup initial workflow state
        self.collection.workflow_status = WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV
        self.collection.save()

        # Step 1: Run fetch_full_text
        with patch("sde_collections.models.collection.Collection.queue_necessary_classifications") as mock_queue:
            fetch_full_text(self.collection.id, "lrm_dev")
            mock_queue.assert_called_once()

        # Verify old DumpUrls were cleared and new ones were also created
        assert not DumpUrl.objects.filter(id=self.existing_dump.id).exists()
        new_dumps = DumpUrl.objects.filter(collection=self.collection)
        assert new_dumps.count() == 2
        assert {dump.url for dump in new_dumps} == {"http://example.com/1", "http://example.com/2"}

        # Step 2: Run migrate_dump_to_delta
        with patch("sde_collections.models.collection.Collection.migrate_dump_to_delta") as mock_migrate:
            migrate_dump_to_delta_and_handle_status_transistions(self.collection.id)
            mock_migrate.assert_called_once()

        # Verify status updates
        self.collection.refresh_from_db()
        assert self.collection.workflow_status == WorkflowStatusChoices.READY_FOR_CURATION


class TestErrorHandling(TransactionTestCase):
    def setUp(self):
        self.collection = CollectionFactory(workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS)

    # The old test_config_creation_failure_handling is gone with the Sinequa trigger it
    # exercised: scrape dispatch is now async (dispatch_scrape_job.delay), so a dispatch
    # failure can no longer abort the status save. Failure handling for the new path
    # (SSM error -> SCRAPING_FAILED, no ScrapeDispatch row) lives in test_scrape_dispatch.py.

    @patch("sde_collections.tasks.Api")
    def test_full_text_fetch_failure_handling(self, MockApi):
        """Test handling of full text fetch failures"""
        mock_api = Mock()
        mock_api.get_full_texts.side_effect = Exception("API error")
        MockApi.return_value = mock_api

        initial_status = self.collection.workflow_status

        with pytest.raises(Exception):
            fetch_full_text(self.collection.id, "lrm_dev")

        # Verify status wasn't changed on error
        self.collection.refresh_from_db()
        assert self.collection.workflow_status == initial_status


NEW_PIPELINE_STATUSES = [
    WorkflowStatusChoices.SCRAPING_SUCCESSFUL,
    WorkflowStatusChoices.TEST_INDEXING,
    WorkflowStatusChoices.SCRAPING_FAILED,
    WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
    WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    WorkflowStatusChoices.PRODUCTION_INDEXING,
]

VALID_BUTTON_COLORS = {
    "btn-light",
    "btn-danger",
    "btn-warning",
    "btn-info",
    "btn-success",
    "btn-primary",
    "btn-secondary",
}


@pytest.mark.parametrize("status", list(WorkflowStatusChoices))
def test_collection_button_color_resolves_for_every_status(status):
    """Regression guard: an unmapped status used to raise KeyError and break the
    collection list and detail pages. Every enum member must resolve a colour."""
    collection = Collection(workflow_status=status)
    assert collection.workflow_status_button_color in VALID_BUTTON_COLORS


@pytest.mark.parametrize("status", list(WorkflowStatusChoices))
def test_workflow_history_button_color_resolves_for_every_status(status):
    history = WorkflowHistory(workflow_status=status)
    assert history.workflow_status_button_color in VALID_BUTTON_COLORS


def test_unmapped_status_falls_back_to_default_color():
    assert Collection(workflow_status=999).workflow_status_button_color == "btn-light"
    assert WorkflowHistory(workflow_status=999).workflow_status_button_color == "btn-light"


@pytest.mark.parametrize(
    "status",
    [
        WorkflowStatusChoices.SCRAPING_FAILED,
        WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
        WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    ],
)
def test_failure_statuses_do_not_render_neutral(status):
    assert Collection(workflow_status=status).workflow_status_button_color == "btn-danger"
    assert WorkflowHistory(workflow_status=status).workflow_status_button_color == "btn-danger"


@pytest.mark.django_db
@pytest.mark.parametrize("status", NEW_PIPELINE_STATUSES)
def test_setting_new_status_writes_workflow_history(status):
    collection = CollectionFactory()
    collection.workflow_status = status
    collection.save()
    assert WorkflowHistory.objects.filter(collection=collection, workflow_status=status).exists()
