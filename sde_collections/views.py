import logging
import re

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CollectionGithubIssueForm, CommentsForm, RequiredUrlForm
from .models.collection import Collection, Comments, RequiredUrls, WorkflowHistory
from .models.collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    OperationChoices,
    ReindexingStatusChoices,
    TDAMMTags,
    WorkflowStatusChoices,
)
from .models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaResolvedTitle,
    DeltaResolvedTitleError,
    DeltaTdammTagPattern,
    DeltaTitlePattern,
)
from .models.delta_url import CuratedUrl, DeltaUrl
from .serializers import (
    CollectionReadSerializer,
    CollectionSerializer,
    CuratedURLAPISerializer,
    CuratedURLSerializer,
    DeltaURLAPISerializer,
    DeltaURLBulkCreateSerializer,
    DeltaURLSerializer,
    DivisionPatternSerializer,
    DocumentTypePatternSerializer,
    ExcludePatternSerializer,
    IncludePatternSerializer,
    TdammTagPatternSerializer,
    TitlePatternSerializer,
)
from .tasks import push_to_github_task
from .utils.health_check import generate_db_github_metadata_differences

User = get_user_model()
logger = logging.getLogger(__name__)


class CollectionListView(LoginRequiredMixin, ListView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_list.html"
    context_object_name = "collections"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(delete=False)
            .annotate(
                num_delta_urls=models.Value(100, output_field=models.IntegerField()),
                num_curated_urls=models.Value(50, output_field=models.IntegerField()),
            )
            .order_by("-num_delta_urls")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collections"
        context["curators"] = User.objects.filter(groups__name="Curators")
        context["curation_status_choices"] = CurationStatusChoices
        context["workflow_status_choices"] = WorkflowStatusChoices
        context["reindexing_status_choices"] = ReindexingStatusChoices

        return context


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """
    Display a list of collections in the system
    """

    model = Collection
    template_name = "sde_collections/collection_detail.html"
    context_object_name = "collection"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        collection = self.get_object()
        form = RequiredUrlForm(request.POST)
        github_form = CollectionGithubIssueForm(request.POST)
        comments_form = CommentsForm(request.POST)

        if "github_issue_link" in request.POST and github_form.is_valid():
            github_issue_link = github_form.cleaned_data["github_issue_link"]
            issue_number = re.search(r"/issues/(\d+)/?$", github_issue_link)
            if issue_number:
                github_issue_number = int(issue_number.group(1))
                collection.github_issue_number = github_issue_number
                collection.save()
            else:
                github_form.add_error("github_issue_link", "Invalid GitHub issue link format")
                return self.render_to_response(self.get_context_data(form=form, github_form=github_form))
            return redirect("sde_collections:detail", pk=collection.pk)

        elif "comment_button" in request.POST and comments_form.is_valid():
            comment = comments_form.save(commit=False)
            comment.collection = collection
            comment.user = self.request.user
            comment.save()
            return redirect("sde_collections:detail", pk=collection.pk)

        else:
            if "claim_button" in request.POST:
                user = self.request.user
                collection.curation_status = WorkflowStatusChoices.CURATION_IN_PROGRESS
                collection.curated_by = user
                collection.curation_started = timezone.now()
                collection.save()
            elif form.is_valid():
                required_url = form.save(commit=False)
                required_url.collection = collection
                required_url.save()
            else:
                # If the form is not valid, render the detail view with the form and errors.
                return self.render_to_response(self.get_context_data(form=form))
            return redirect("sde_collections:detail", pk=collection.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in context:
            context["form"] = RequiredUrlForm()
        if "github_form" not in context:
            context["github_form"] = CollectionGithubIssueForm(
                initial={"github_issue_link": self.get_object().github_issue_link}
            )
        if "comments_form" not in context:
            context["comments_form"] = CommentsForm()

        # Initialize a dictionary to hold the most recent history for each workflow status
        timeline_history = {}

        # Get the most recent history for each workflow status
        recent_histories = (
            WorkflowHistory.objects.filter(collection=self.get_object())
            .order_by("workflow_status", "-created_at")
            .distinct("workflow_status")
        )

        # Populate the dictionary with the actual history objects
        for history in recent_histories:
            timeline_history[history.workflow_status] = history

        # Add placeholders for stages with no workflow history
        for workflow_status in WorkflowStatusChoices:
            if workflow_status not in timeline_history:
                timeline_history[workflow_status] = {
                    "workflow_status": workflow_status,
                    "created_at": None,
                    "label": WorkflowStatusChoices(workflow_status).label,
                }

        context["timeline_history"] = [timeline_history[workflow_status] for workflow_status in WorkflowStatusChoices]
        context["required_urls"] = RequiredUrls.objects.filter(collection=self.get_object())
        context["segment"] = "collection-detail"
        context["comments"] = Comments.objects.filter(collection=self.get_object()).order_by("-created_at")
        context["workflow_history"] = WorkflowHistory.objects.filter(collection=self.get_object()).order_by(
            "-created_at"
        )
        context["workflow_status_choices"] = WorkflowStatusChoices
        context["reindexing_status_choices"] = ReindexingStatusChoices

        return context


class RequiredUrlsDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredUrls

    def get_success_url(self, *args, **kwargs):
        return reverse("sde_collections:detail", kwargs={"pk": self.object.collection.pk})


class DeltaURLsListView(LoginRequiredMixin, ListView):
    """
    Display a list of collections in the system
    """

    model = DeltaUrl
    template_name = "sde_collections/delta_urls_list.html"
    context_object_name = "delta_urls"
    # paginate_by = 1000

    def _filter_by_is_exluded(self, queryset, is_excluded):
        if is_excluded == "true":
            queryset = queryset.filter(appliedexclude__isnull=False)
        elif is_excluded == "false":
            queryset = queryset.exclude(appliedexclude__isnull=False)
        return queryset

    def get_queryset(self):
        self.collection = Collection.objects.get(pk=self.kwargs["pk"])
        queryset = super().get_queryset().filter(collection=self.collection)

        # Filter based on exclusion status
        is_excluded = self.request.GET.get("is_excluded")
        if is_excluded:
            queryset = self._filter_by_is_exluded(queryset, is_excluded)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "delta-url-list"
        context["collection"] = self.collection
        context["regex_exclude_patterns"] = self.collection.excludepattern.filter(
            match_pattern_type=2
        )  # 2=regex patterns
        context["title_patterns"] = self.collection.titlepattern.all()
        context["workflow_status_choices"] = WorkflowStatusChoices
        context["reindexing_status_choices"] = ReindexingStatusChoices
        context["is_multi_division"] = self.collection.is_multi_division
        context["has_tdamm_tags"] = self.collection.has_tdamm_tags()

        tdamm_choices = [
            {"code": choice[0], "label": choice[1], "display": f"{choice[0]}: {choice[1]}"}
            for choice in TDAMMTags.choices
            # if choice[0] != 'Not TDAMM'
        ]
        context["tdamm_choices"] = tdamm_choices

        # print("TDAMM choices:", context['tdamm_choices'])

        return context


class SdeDashboardView(LoginRequiredMixin, ListView):
    model = Collection
    template_name = "sde_collections/sde_dashboard.html"
    context_object_name = "collections"

    def get_queryset(self):
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collections"
        return context


class CollectionFilterMixin:
    def get_queryset(self):
        if not self.request.method == "GET":
            return super().get_queryset()

        try:
            collection_id = self.request.GET.get("collection_id")
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            # just return an empty list
            return super().get_queryset().filter(collection__isnull=True)
        return super().get_queryset().filter(collection=collection)


class DeltaURLViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaUrl.objects.all()
    serializer_class = DeltaURLSerializer

    def _filter_by_is_excluded(self, queryset, is_excluded):
        if is_excluded == "false":
            queryset = queryset.filter(excluded=False)
        elif is_excluded == "true":
            queryset = queryset.exclude(excluded=False)
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            collection_id = self.request.GET.get("collection_id")
            # Filter based on exclusion status
            is_excluded = self.request.GET.get("is_excluded")
            if is_excluded:
                queryset = self._filter_by_is_excluded(queryset, is_excluded)

            # Annotate queryset with two pieces of information:
            # 1. exclude_pattern_type: Type of exclude pattern (1=Individual URL, 2=Multi-URL Pattern)
            #    Ordered by -match_pattern_type to prioritize multi-url patterns (type 2)
            # 2. include_pattern_id: ID of any include pattern affecting this URL
            #    Used when we need to delete the include pattern during re-exclusion
            queryset = queryset.annotate(
                exclude_pattern_type=models.Subquery(
                    DeltaExcludePattern.objects.filter(delta_urls=models.OuterRef("pk"), collection_id=collection_id)
                    .order_by("-match_pattern_type")
                    .values("match_pattern_type")[:1]
                ),
                include_pattern_id=models.Subquery(
                    DeltaIncludePattern.objects.filter(
                        delta_urls=models.OuterRef("pk"), collection_id=collection_id
                    ).values("id")[:1]
                ),
            )

        return queryset.order_by("url")

    def update_division(self, request, pk=None):
        delta_url = get_object_or_404(DeltaUrl, pk=pk)
        division = request.data.get("division")
        if division:
            delta_url.division = division
            delta_url.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Division is required."})

    # @action(detail=True, methods=["post"], url_path="add_tag")
    # def add_tag(self, request, pk=None):
    #     delta_url = self.get_object()
    #     tag = request.data.get("tag")
    #     source = request.data.get("source", "manual")

    #     if not tag:
    #         return Response({"error": "Tag not specified"}, status=400)

    #     try:
    #         # Create or get a pattern for this specific URL
    #         pattern, created = DeltaTdammTagPattern.objects.get_or_create(
    #             collection=delta_url.collection,
    #             match_pattern=delta_url.url,
    #             match_pattern_type=1,
    #             # tag=tag,
    #             operation=OperationChoices.ADD,
    #             source=source,
    #             defaults={"tags": [tag]},
    #         )

    #         if not created:
    #             # Add tag if not already present
    #             current_tags = pattern.tags or []
    #             if tag not in current_tags:
    #                 pattern.tags = current_tags + [tag]
    #                 pattern.save()

    #         # Remove from REMOVE pattern if it exists
    #         remove_pattern = DeltaTdammTagPattern.objects.filter(
    #             collection=delta_url.collection,
    #             match_pattern=delta_url.url,
    #             operation=OperationChoices.REMOVE,
    #             source=source,
    #         ).first()

    #         if remove_pattern and remove_pattern.tags and tag in remove_pattern.tags:
    #             # Remove this tag from the remove pattern
    #             remove_pattern.tags = [t for t in remove_pattern.tags if t != tag]
    #             if not remove_pattern.tags:
    #                 remove_pattern.delete()
    #             else:
    #                 remove_pattern.save()

    #         # Apply the pattern
    #         pattern._apply_tag_operation(delta_url)

    #         return Response({"status": "success"})
    #     except Exception as e:
    #         logger.error(f"Error occurred: {str(e)}")
    #         return Response({"error": "An internal error has occurred."}, status=500)

    @action(detail=True, methods=["post"], url_path="add_tag")
    def add_tag(self, request, pk=None):
        delta_url = self.get_object()
        tag = request.data.get("tag")
        source = request.data.get("source", "manual")

        if not tag:
            return Response({"error": "Tag not specified"}, status=400)

        try:
            # Get current manual and ML tags
            manual_tags = delta_url.tdamm_tag_manual
            ml_tags = delta_url.tdamm_tag_ml or []

            logger.info(f"Adding tag '{tag}' to URL: {delta_url.url}")
            logger.info(f"Current manual tags: {manual_tags}")
            logger.info(f"Current ML tags: {ml_tags}")

            # STEP 1: Update URL's manual tags

            # Case 3: No manual tags, but ML tags exist - copy ML tags to manual
            if (manual_tags is None or len(manual_tags) == 0) and ml_tags:
                logger.info("No manual tags, but ML tags exist - copying ML tags to manual")
                working_tags = list(ml_tags)
            # Case 1 & 2: Empty or existing manual tags
            else:
                working_tags = list(manual_tags) if manual_tags is not None else []

            # Add the new tag if not already present
            if tag not in working_tags:
                working_tags.append(tag)
                delta_url.tdamm_tag_manual = working_tags
                delta_url.save()
                logger.info(f"Updated URL tags to: {working_tags}")

            # STEP 2: Find or update ADD pattern

            # Look for existing ADD patterns for this URL
            existing_patterns = list(
                DeltaTdammTagPattern.objects.filter(
                    collection=delta_url.collection,
                    match_pattern=delta_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                )
            )

            logger.info(f"Found {len(existing_patterns)} existing ADD patterns")

            # Update existing pattern or create new one
            if existing_patterns:
                # Use the first pattern found
                add_pattern = existing_patterns[0]
                logger.info(f"Updating existing pattern {add_pattern.id}, current tags: {add_pattern.tags}")

                # Ensure pattern has all current tags
                pattern_tags = set(add_pattern.tags or [])
                for current_tag in working_tags:
                    pattern_tags.add(current_tag)

                add_pattern.tags = list(pattern_tags)
                add_pattern.source = source  # Update source to match current request
                add_pattern.save()
                logger.info(f"Updated pattern tags to: {add_pattern.tags}")

                # Delete any other duplicate patterns
                for pattern in existing_patterns[1:]:
                    logger.info(f"Deleting duplicate pattern {pattern.id}")
                    pattern.delete()
            else:
                # Create a new pattern with all working tags
                logger.info(f"Creating new ADD pattern with tags: {working_tags}")
                add_pattern = DeltaTdammTagPattern.objects.create(
                    collection=delta_url.collection,
                    match_pattern=delta_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                    source=source,
                    tags=working_tags,
                )
                logger.info(f"Created pattern {add_pattern.id}")

            # STEP 3: Check for and update any REMOVE patterns

            remove_patterns = DeltaTdammTagPattern.objects.filter(
                collection=delta_url.collection,
                match_pattern=delta_url.url,
                match_pattern_type=1,
                operation=OperationChoices.REMOVE,
            )

            for remove_pattern in remove_patterns:
                if remove_pattern.tags and tag in remove_pattern.tags:
                    remove_pattern.tags = [t for t in remove_pattern.tags if t != tag]
                    if not remove_pattern.tags:
                        logger.info(f"Deleting empty REMOVE pattern {remove_pattern.id}")
                        remove_pattern.delete()
                    else:
                        logger.info(f"Updated REMOVE pattern {remove_pattern.id} to {remove_pattern.tags}")
                        remove_pattern.save()

            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({"error": f"An internal error has occurred: {str(e)}"}, status=500)

    # @action(detail=True, methods=["post"], url_path="remove_tag")
    # def remove_tag(self, request, pk=None):
    #     delta_url = self.get_object()
    #     tag = request.data.get("tag")
    #     source = request.data.get("source", "manual")

    #     if not tag:
    #         return Response({"error": "Tag not specified"}, status=400)

    #     try:
    #         # Create or get a pattern for this specific URL
    #         pattern, created = DeltaTdammTagPattern.objects.get_or_create(
    #             collection=delta_url.collection,
    #             match_pattern=delta_url.url,
    #             match_pattern_type=1,
    #             # tag=tag,
    #             operation=OperationChoices.REMOVE,
    #             source=source,
    #             defaults={"tags": [tag]},
    #         )

    #         if not created:
    #             # Add tag to remove list if not already present
    #             current_tags = pattern.tags or []
    #             if tag not in current_tags:
    #                 pattern.tags = current_tags + [tag]
    #                 pattern.save()

    #         # Remove from ADD pattern if it exists
    #         add_pattern = DeltaTdammTagPattern.objects.filter(
    #             collection=delta_url.collection,
    #             match_pattern=delta_url.url,
    #             operation=OperationChoices.ADD,
    #             source=source,
    #         ).first()

    #         if add_pattern and add_pattern.tags and tag in add_pattern.tags:
    #             # Remove this tag from the add pattern
    #             add_pattern.tags = [t for t in add_pattern.tags if t != tag]
    #             if not add_pattern.tags:
    #                 add_pattern.delete()
    #             else:
    #                 add_pattern.save()

    #         # Apply the pattern
    #         pattern._apply_tag_operation(delta_url)

    #         return Response({"status": "success"})
    #     except Exception as e:
    #         logger.error(f"Error occurred: {str(e)}")
    #         return Response({"error": "An internal error has occurred."}, status=500)

    @action(detail=True, methods=["post"], url_path="remove_tag")
    def remove_tag(self, request, pk=None):
        delta_url = self.get_object()
        tag = request.data.get("tag")
        source = request.data.get("source", "manual")

        if not tag:
            return Response({"error": "Tag not specified"}, status=400)

        try:
            # Get current tags
            manual_tags = delta_url.tdamm_tag_manual or []
            ml_tags = delta_url.tdamm_tag_ml or []

            # First, let's log what patterns exist for debugging
            logger.info(f"Looking for patterns matching URL: {delta_url.url}")

            # Find ALL add patterns that might contain this tag
            add_patterns = list(
                DeltaTdammTagPattern.objects.filter(
                    collection=delta_url.collection,
                    match_pattern=delta_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                    source=source,
                )
            )

            logger.info(f"Found {len(add_patterns)} ADD patterns")
            for pat in add_patterns:
                logger.info(f"ADD pattern {pat.id}: tags={pat.tags}")

            # Flag to track if we modified an ADD pattern
            modified_add_pattern = False

            # Check ALL add patterns (there might be duplicates)
            for add_pattern in add_patterns:
                if add_pattern.tags and tag in add_pattern.tags:
                    logger.info(f"Modifying ADD pattern {add_pattern.id}")

                    # Remove the tag from the pattern's tags
                    add_pattern.tags = [t for t in add_pattern.tags if t != tag]

                    # Save or delete the pattern
                    if not add_pattern.tags:
                        logger.info(f"Deleting empty ADD pattern {add_pattern.id}")
                        add_pattern.delete()
                    else:
                        logger.info(f"Saving ADD pattern {add_pattern.id} with tags {add_pattern.tags}")
                        add_pattern.save()

                    modified_add_pattern = True

            # Always update the URL's tags to remove the tag
            if tag in manual_tags:
                new_tags = [t for t in manual_tags if t != tag]
                # Set to None if empty, not empty list
                delta_url.tdamm_tag_manual = new_tags if new_tags else None
                delta_url.save()
                logger.info(f"Updated URL tags: {delta_url.tdamm_tag_manual}")

            # If we modified an ADD pattern, we're done - no need for a REMOVE pattern
            if modified_add_pattern:
                return Response({"status": "success"})

            # Only create a REMOVE pattern if tag is in ML tags
            if tag in ml_tags:
                logger.info(f"Creating/updating REMOVE pattern for ML tag {tag}")

                # Find existing REMOVE patterns
                remove_patterns = list(
                    DeltaTdammTagPattern.objects.filter(
                        collection=delta_url.collection,
                        match_pattern=delta_url.url,
                        match_pattern_type=1,
                        operation=OperationChoices.REMOVE,
                        source=source,
                    )
                )

                logger.info(f"Found {len(remove_patterns)} REMOVE patterns")

                if remove_patterns:
                    # Update the first REMOVE pattern
                    remove_pattern = remove_patterns[0]
                    current_tags = remove_pattern.tags or []
                    if tag not in current_tags:
                        remove_pattern.tags = current_tags + [tag]
                        remove_pattern.save()
                        logger.info(f"Updated REMOVE pattern {remove_pattern.id} with tags {remove_pattern.tags}")
                else:
                    # Create new REMOVE pattern
                    remove_pattern = DeltaTdammTagPattern.objects.create(
                        collection=delta_url.collection,
                        match_pattern=delta_url.url,
                        match_pattern_type=1,
                        operation=OperationChoices.REMOVE,
                        source=source,
                        tags=[tag],
                    )
                    logger.info(f"Created new REMOVE pattern {remove_pattern.id} with tag {tag}")

            # Call cleanup if needed
            if hasattr(delta_url, "_cleanup_if_needed"):
                delta_url._cleanup_if_needed()

            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({"error": f"An internal error has occurred: {str(e)}"}, status=500)

    # def _refresh_url_tags(self, url_obj):
    #     """Refresh URL tags by reapplying all patterns affecting this URL."""
    #     # Get all patterns affecting this URL
    #     add_patterns = DeltaTdammTagPattern.objects.filter(
    #         collection=url_obj.collection, delta_urls=url_obj, operation=OperationChoices.ADD
    #     )

    #     remove_patterns = DeltaTdammTagPattern.objects.filter(
    #         collection=url_obj.collection, delta_urls=url_obj, operation=OperationChoices.REMOVE
    #     )

    #     # Collect all tags from ADD patterns
    #     add_tags = set()
    #     for pattern in add_patterns:
    #         add_tags.update(pattern.tags or [])

    #     # Collect all tags from REMOVE patterns
    #     remove_tags = set()
    #     for pattern in remove_patterns:
    #         remove_tags.update(pattern.tags or [])

    #     # Final tags = (add tags) - (remove tags)
    #     final_tags = list(add_tags - remove_tags)

    #     # Update URL tags
    #     url_obj.tdamm_tag_manual = final_tags if final_tags else None
    #     url_obj.save()


class CuratedURLViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = CuratedUrl.objects.all()
    serializer_class = CuratedURLSerializer

    def _filter_by_is_excluded(self, queryset, is_excluded):
        if is_excluded == "false":
            queryset = queryset.filter(excluded=False)
        elif is_excluded == "true":
            queryset = queryset.exclude(excluded=False)
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            # Filter based on exclusion status
            is_excluded = self.request.GET.get("is_excluded")
            if is_excluded:
                queryset = self._filter_by_is_excluded(queryset, is_excluded)
        return queryset.order_by("url")

    def update_division(self, request, pk=None):
        delta_url = get_object_or_404(CuratedUrl, pk=pk)
        division = request.data.get("division")
        if division:
            delta_url.division = division
            delta_url.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Division is required."})

    # @action(detail=True, methods=["post"], url_path="add_tag")
    # def add_tag(self, request, pk=None):
    #     curated_url = self.get_object()
    #     tag = request.data.get("tag")
    #     source = request.data.get("source", "manual")

    #     if not tag:
    #         return Response({"error": "Tag not specified"}, status=400)

    #     try:
    #         # Create delta URL first
    #         delta_url = curated_url._create_or_update_delta()

    #         # Then apply tag operations to the delta
    #         pattern, created = DeltaTdammTagPattern.objects.get_or_create(
    #             collection=curated_url.collection,
    #             match_pattern=curated_url.url,
    #             match_pattern_type=1,
    #             operation=OperationChoices.ADD,
    #             source=source,
    #             defaults={"tags": [tag]},
    #         )

    #         if not created:
    #             # Add tag if not already present
    #             current_tags = pattern.tags or []
    #             if tag not in current_tags:
    #                 pattern.tags = current_tags + [tag]
    #                 pattern.save()

    #         if not created:
    #             # Add tag if not already present
    #             current_tags = pattern.tags or []
    #             if tag not in current_tags:
    #                 pattern.tags = current_tags + [tag]
    #                 pattern.save()

    #         # Remove from REMOVE pattern if it exists
    #         remove_pattern = DeltaTdammTagPattern.objects.filter(
    #             collection=delta_url.collection,
    #             match_pattern=delta_url.url,
    #             operation=OperationChoices.REMOVE,
    #             source=source,
    #         ).first()

    #         if remove_pattern and remove_pattern.tags and tag in remove_pattern.tags:
    #             # Remove this tag from the remove pattern
    #             remove_pattern.tags = [t for t in remove_pattern.tags if t != tag]
    #             if not remove_pattern.tags:
    #                 remove_pattern.delete()
    #             else:
    #                 remove_pattern.save()

    #         pattern._apply_tag_operation(delta_url)

    #         # Clean up if delta becomes identical to curated
    #         if not delta_url.to_delete and delta_url._fields_match(curated_url):
    #             delta_url.delete()

    #         return Response({"status": "success"})
    #     except Exception as e:
    #         logger.error(f"Error occurred: {str(e)}")
    #         return Response({"error": "An internal error has occurred."}, status=500)

    @action(detail=True, methods=["post"], url_path="add_tag")
    def add_tag(self, request, pk=None):
        curated_url = self.get_object()
        tag = request.data.get("tag")
        source = request.data.get("source", "manual")

        if not tag:
            return Response({"error": "Tag not specified"}, status=400)

        try:
            # Create delta URL first
            delta_url = curated_url._create_or_update_delta()

            # Get current manual and ML tags
            manual_tags = delta_url.tdamm_tag_manual
            ml_tags = curated_url.tdamm_tag_ml or []

            logger.info(f"Adding tag '{tag}' to URL: {curated_url.url}")
            logger.info(f"Current manual tags: {manual_tags}")
            logger.info(f"Current ML tags: {ml_tags}")

            # STEP 1: Update URL's manual tags

            # Case 3: No manual tags, but ML tags exist - copy ML tags to manual
            if (manual_tags is None or len(manual_tags) == 0) and ml_tags:
                logger.info("No manual tags, but ML tags exist - copying ML tags to manual")
                working_tags = list(ml_tags)
            # Case 1 & 2: Empty or existing manual tags
            else:
                working_tags = list(manual_tags) if manual_tags is not None else []

            # Add the new tag if not already present
            if tag not in working_tags:
                working_tags.append(tag)
                delta_url.tdamm_tag_manual = working_tags
                delta_url.save()
                logger.info(f"Updated URL tags to: {working_tags}")

            # STEP 2: Find or update ADD pattern

            # Look for existing ADD patterns for this URL
            existing_patterns = list(
                DeltaTdammTagPattern.objects.filter(
                    collection=curated_url.collection,
                    match_pattern=curated_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                )
            )

            logger.info(f"Found {len(existing_patterns)} existing ADD patterns")

            # Update existing pattern or create new one
            if existing_patterns:
                # Use the first pattern found
                add_pattern = existing_patterns[0]
                logger.info(f"Updating existing pattern {add_pattern.id}, current tags: {add_pattern.tags}")

                # Ensure pattern has all current tags
                pattern_tags = set(add_pattern.tags or [])
                for current_tag in working_tags:
                    pattern_tags.add(current_tag)

                add_pattern.tags = list(pattern_tags)
                add_pattern.source = source  # Update source to match current request
                add_pattern.save()
                logger.info(f"Updated pattern tags to: {add_pattern.tags}")

                # Delete any other duplicate patterns
                for pattern in existing_patterns[1:]:
                    logger.info(f"Deleting duplicate pattern {pattern.id}")
                    pattern.delete()
            else:
                # Create a new pattern with all working tags
                logger.info(f"Creating new ADD pattern with tags: {working_tags}")
                add_pattern = DeltaTdammTagPattern.objects.create(
                    collection=curated_url.collection,
                    match_pattern=curated_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                    source=source,
                    tags=working_tags,
                )
                logger.info(f"Created pattern {add_pattern.id}")

            # STEP 3: Check for and update any REMOVE patterns

            remove_patterns = DeltaTdammTagPattern.objects.filter(
                collection=curated_url.collection,
                match_pattern=curated_url.url,
                match_pattern_type=1,
                operation=OperationChoices.REMOVE,
            )

            for remove_pattern in remove_patterns:
                if remove_pattern.tags and tag in remove_pattern.tags:
                    remove_pattern.tags = [t for t in remove_pattern.tags if t != tag]
                    if not remove_pattern.tags:
                        logger.info(f"Deleting empty REMOVE pattern {remove_pattern.id}")
                        remove_pattern.delete()
                    else:
                        logger.info(f"Updated REMOVE pattern {remove_pattern.id} to {remove_pattern.tags}")
                        remove_pattern.save()

            # Clean up delta if it matches curated
            if not delta_url.to_delete and delta_url._fields_match(curated_url):
                logger.info(f"Deleting delta URL {delta_url.url} as it matches curated URL")
                delta_url.delete()

            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({"error": f"An internal error has occurred: {str(e)}"}, status=500)

    # @action(detail=True, methods=["post"], url_path="remove_tag")
    # def remove_tag(self, request, pk=None):
    #     curated_url = self.get_object()
    #     tag = request.data.get("tag")
    #     source = request.data.get("source", "manual")

    #     if not tag:
    #         return Response({"error": "Tag not specified"}, status=400)

    #     try:
    #         # Create delta URL first
    #         delta_url = curated_url._create_or_update_delta()

    #         # Create or get a pattern for tag removal
    #         pattern, created = DeltaTdammTagPattern.objects.get_or_create(
    #             collection=curated_url.collection,
    #             match_pattern=curated_url.url,
    #             match_pattern_type=1,
    #             operation=DeltaTdammTagPattern.OperationChoices.REMOVE,
    #             source=source,
    #             defaults={"tags": [tag]},
    #         )

    #         if not created:
    #             # Add tag to removal list if not already present
    #             current_tags = pattern.tags or []
    #             if tag not in current_tags:
    #                 pattern.tags = current_tags + [tag]
    #                 pattern.save()

    #         # Check for and update ADD pattern if it exists
    #         add_pattern = DeltaTdammTagPattern.objects.filter(
    #             collection=curated_url.collection,
    #             match_pattern=curated_url.url,
    #             operation=DeltaTdammTagPattern.OperationChoices.ADD,
    #             source=source,
    #         ).first()

    #         if add_pattern and add_pattern.tags and tag in add_pattern.tags:
    #             # Remove tag from add pattern
    #             add_pattern.tags = [t for t in add_pattern.tags if t != tag]
    #             if not add_pattern.tags:
    #                 add_pattern.delete()
    #             else:
    #                 add_pattern.save()

    #         # Apply the pattern
    #         pattern._apply_tag_operation(delta_url)

    #         # Clean up if delta becomes identical to curated
    #         if not delta_url.to_delete and delta_url._fields_match(curated_url):
    #             delta_url.delete()

    #         return Response({"status": "success"})
    #     except Exception as e:
    #         logger.error(f"Error occurred: {str(e)}")
    #         return Response({"error": "An internal error has occurred."}, status=500)

    @action(detail=True, methods=["post"], url_path="remove_tag")
    def remove_tag(self, request, pk=None):
        curated_url = self.get_object()
        tag = request.data.get("tag")
        source = request.data.get("source", "manual")

        if not tag:
            return Response({"error": "Tag not specified"}, status=400)

        try:
            # Create delta URL first
            delta_url = curated_url._create_or_update_delta()

            # Get current tags
            manual_tags = delta_url.tdamm_tag_manual or []
            ml_tags = curated_url.tdamm_tag_ml or []

            # First, let's log what patterns exist for debugging
            logger.info(f"Looking for patterns matching URL: {curated_url.url}")

            # Find ALL add patterns that might contain this tag
            add_patterns = list(
                DeltaTdammTagPattern.objects.filter(
                    collection=curated_url.collection,
                    match_pattern=curated_url.url,
                    match_pattern_type=1,
                    operation=OperationChoices.ADD,
                    source=source,
                )
            )

            logger.info(f"Found {len(add_patterns)} ADD patterns")
            for pat in add_patterns:
                logger.info(f"ADD pattern {pat.id}: tags={pat.tags}")

            # Flag to track if we modified an ADD pattern
            modified_add_pattern = False

            # Check ALL add patterns (there might be duplicates)
            for add_pattern in add_patterns:
                if add_pattern.tags and tag in add_pattern.tags:
                    logger.info(f"Modifying ADD pattern {add_pattern.id}")

                    # Remove the tag from the pattern's tags
                    add_pattern.tags = [t for t in add_pattern.tags if t != tag]

                    # Save or delete the pattern
                    if not add_pattern.tags:
                        logger.info(f"Deleting empty ADD pattern {add_pattern.id}")
                        add_pattern.delete()
                    else:
                        logger.info(f"Saving ADD pattern {add_pattern.id} with tags {add_pattern.tags}")
                        add_pattern.save()

                    modified_add_pattern = True

            # Always update the URL's tags to remove the tag
            if tag in manual_tags:
                new_tags = [t for t in manual_tags if t != tag]
                # Set to None if empty, not empty list
                delta_url.tdamm_tag_manual = new_tags if new_tags else None
                delta_url.save()
                logger.info(f"Updated URL tags: {delta_url.tdamm_tag_manual}")

            # If we modified an ADD pattern and there are no tags left, possibly we can delete the delta
            if modified_add_pattern and (delta_url.tdamm_tag_manual is None or len(delta_url.tdamm_tag_manual) == 0):
                # Check if the delta can be deleted
                if not delta_url.to_delete and delta_url._fields_match(curated_url):
                    logger.info(f"Deleting delta URL {delta_url.id} as it matches curated URL")
                    delta_url.delete()
                    return Response({"status": "success"})

            # If we modified an ADD pattern, we're done - no need for a REMOVE pattern
            if modified_add_pattern:
                return Response({"status": "success"})

            # Only create a REMOVE pattern if tag is in ML tags
            if tag in ml_tags:
                logger.info(f"Creating/updating REMOVE pattern for ML tag {tag}")

                # Find existing REMOVE patterns
                remove_patterns = list(
                    DeltaTdammTagPattern.objects.filter(
                        collection=curated_url.collection,
                        match_pattern=curated_url.url,
                        match_pattern_type=1,
                        operation=OperationChoices.REMOVE,
                        source=source,
                    )
                )

                logger.info(f"Found {len(remove_patterns)} REMOVE patterns")

                if remove_patterns:
                    # Update the first REMOVE pattern
                    remove_pattern = remove_patterns[0]
                    current_tags = remove_pattern.tags or []
                    if tag not in current_tags:
                        remove_pattern.tags = current_tags + [tag]
                        remove_pattern.save()
                        logger.info(f"Updated REMOVE pattern {remove_pattern.id} with tags {remove_pattern.tags}")
                else:
                    # Create new REMOVE pattern
                    remove_pattern = DeltaTdammTagPattern.objects.create(
                        collection=curated_url.collection,
                        match_pattern=curated_url.url,
                        match_pattern_type=1,
                        operation=OperationChoices.REMOVE,
                        source=source,
                        tags=[tag],
                    )
                    logger.info(f"Created new REMOVE pattern {remove_pattern.id} with tag {tag}")

            # Clean up if delta becomes identical to curated
            if not delta_url.to_delete and delta_url._fields_match(curated_url):
                logger.info(f"Deleting delta URL {delta_url.id} as it matches curated URL")
                delta_url.delete()

            return Response({"status": "success"})
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({"error": f"An internal error has occurred: {str(e)}"}, status=500)

    # def _refresh_url_tags(self, url_obj):
    #     """Refresh URL tags by reapplying all patterns affecting this URL."""
    #     # Get all patterns affecting this URL
    #     add_patterns = DeltaTdammTagPattern.objects.filter(
    #         collection=url_obj.collection, delta_urls=url_obj, operation=OperationChoices.ADD
    #     )

    #     remove_patterns = DeltaTdammTagPattern.objects.filter(
    #         collection=url_obj.collection, delta_urls=url_obj, operation=OperationChoices.REMOVE
    #     )

    #     # Collect all tags from ADD patterns
    #     add_tags = set()
    #     for pattern in add_patterns:
    #         add_tags.update(pattern.tags or [])

    #     # Collect all tags from REMOVE patterns
    #     remove_tags = set()
    #     for pattern in remove_patterns:
    #         remove_tags.update(pattern.tags or [])

    #     # Final tags = (add tags) - (remove tags)
    #     final_tags = list(add_tags - remove_tags)

    #     # Update URL tags
    #     url_obj.tdamm_tag_manual = final_tags if final_tags else None
    #     url_obj.save()


class DeltaURLBulkCreateView(generics.ListCreateAPIView):
    queryset = DeltaUrl.objects.all()
    serializer_class = DeltaURLBulkCreateSerializer

    def perform_create(self, serializer, collection_id=None):
        for validated_data in serializer.validated_data:
            validated_data["collection_id"] = collection_id
        super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        collection = Collection.objects.get(config_folder=config_folder)
        collection.delta_urls.all().delete()

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, collection_id=collection.pk)

        collection.apply_all_patterns()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DeltaURLAPIView(ListAPIView):
    serializer_class = DeltaURLAPISerializer

    def get(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        self.config_folder = config_folder
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            DeltaUrl.objects.filter(collection__config_folder=self.config_folder)
            .with_exclusion_status()
            .filter(excluded=False)
        )
        return queryset


class CuratedURLAPIView(ListAPIView):
    serializer_class = CuratedURLAPISerializer

    def get(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        self.config_folder = config_folder
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            CuratedUrl.objects.filter(collection__config_folder=self.config_folder)
            .with_exclusion_status()
            .filter(excluded=False)
        )
        return queryset


class ExcludePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaExcludePattern.objects.all()
    serializer_class = ExcludePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        match_pattern = request.POST.get("match_pattern")
        collection_id = request.POST.get("collection")
        try:
            DeltaExcludePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except DeltaExcludePattern.DoesNotExist:
            return super().create(request, *args, **kwargs)


class IncludePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaIncludePattern.objects.all()
    serializer_class = IncludePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        match_pattern = request.POST.get("match_pattern")
        collection_id = request.POST.get("collection")
        try:
            DeltaIncludePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except DeltaIncludePattern.DoesNotExist:
            return super().create(request, *args, **kwargs)


class TitlePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaTitlePattern.objects.all()
    serializer_class = TitlePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")


class DocumentTypePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaDocumentTypePattern.objects.all()
    serializer_class = DocumentTypePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        document_type = request.POST.get("document_type")
        if not int(document_type) == 0:  # 0=none
            return super().create(request, *args, **kwargs)
        else:
            collection_id = request.POST.get("collection")
            match_pattern = request.POST.get("match_pattern")
            try:
                DeltaDocumentTypePattern.objects.get(
                    collection_id=Collection.objects.get(id=collection_id),
                    match_pattern=match_pattern,
                    match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
                ).delete()
                return Response(status=status.HTTP_200_OK)
            except DeltaDocumentTypePattern.DoesNotExist:
                return Response(status=status.HTTP_204_NO_CONTENT)


class DivisionPatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaDivisionPattern.objects.all()
    serializer_class = DivisionPatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        division = request.POST.get("division")
        if division:
            return super().create(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Division is required."})


# class TdammTagPatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
#     queryset = DeltaTdammTagPattern.objects.all()
#     serializer_class = TdammTagPatternSerializer

#     def get_queryset(self):
#         return super().get_queryset().order_by("match_pattern")


class TdammTagPatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DeltaTdammTagPattern.objects.all()
    serializer_class = TdammTagPatternSerializer

    # def create(self, request, *args, **kwargs):
    #     # Handle single tag parameter from frontend
    #     tag = request.data.get('tag')
    #     if tag:
    #         # Make a mutable copy of the data
    #         data = request.data.copy()
    #         # Convert single tag to tags array
    #         data['tags'] = [tag]
    #         # Use this modified data for serialization
    #         serializer = self.get_serializer(data=data)
    #         serializer.is_valid(raise_exception=True)
    #         self.perform_create(serializer)
    #         headers = self.get_success_headers(serializer.data)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #     return super().create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        if "tag" in data:
            tag = data.pop("tag")
            data["tags"] = [tag]

        # Create serializer with cleaned data
        serializer = self.get_serializer(data=data)

        # Print data for debugging
        print(f"Data going to serializer: {data}")

        # Continue with validation and creation
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class CollectionReadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionReadSerializer


class PushToGithubView(APIView):
    def post(self, request):
        collection_ids = request.POST.getlist("collection_ids[]", [])
        if len(collection_ids) == 0:
            return Response("collection_ids can't be empty.", status=status.HTTP_400_BAD_REQUEST)

        push_to_github_task.delay(collection_ids)

        return Response(
            {"Success": "Started pushing collections to github"},
            status=status.HTTP_200_OK,
        )


class IndexingInstructionsView(APIView):
    """
    Serves the name of the first curated collection to be indexed and updates collection workflow status
    """

    def get(self, request):
        curated_collections = Collection.objects.filter(workflow_status=WorkflowStatusChoices.CURATED)

        job_name = ""
        if curated_collections.exists():
            collection = curated_collections.first()
            job_name = f"collection.indexer.{collection.config_folder}.xml"

        return Response(
            {
                "job_name": job_name,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        config_folder = request.data.get("collection")
        indexing_status = request.data.get("status")

        if not config_folder or not indexing_status:
            raise ValidationError({"error": "Config folder name and indexing status are required."})

        collection = get_object_or_404(Collection, config_folder=config_folder)

        if indexing_status == "STARTED_INDEXING" and collection.workflow_status == WorkflowStatusChoices.CURATED:
            collection.workflow_status = WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED
            collection.save()

            return Response(
                {"message": f"Status for collection '{collection.name}' updated to Secret Deployment Started."},
                status=status.HTTP_200_OK,
            )
        elif (
            indexing_status == "FINISHED_INDEXING"
            and collection.workflow_status == WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED
        ):
            collection.workflow_status = WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK
            collection.save()

            return Response(
                {"message": f"Status for collection '{collection.name}' updated to Ready For LRM Quality Check."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"error": "Invalid indexing or workflow status."}, status=status.HTTP_400_BAD_REQUEST)


class WebappGitHubConsolidationView(LoginRequiredMixin, TemplateView):
    """
    Display a list of collections in the system
    """

    template_name = "sde_collections/consolidate_db_and_github_configs.html"

    def get(self, request, *args, **kwargs):
        if not request.GET.get("reindex") == "true":
            self.data = generate_db_github_metadata_differences()
        else:
            # this needs to be a celery task eventually
            self.data = generate_db_github_metadata_differences(reindex_configs_from_github=True)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        config_folder = self.request.POST.get("config_folder")
        field = self.request.POST.get("field")
        new_value = self.request.POST.get("github_value")

        if new_value and new_value != "None":
            new_value = new_value.strip()
            if field == "division":
                new_value = Divisions.lookup_by_text(new_value)
            elif field == "document_type":
                new_value = DocumentTypes.lookup_by_text(new_value)
            elif field == "connector":
                new_value = ConnectorChoices.lookup_by_text(new_value)

            Collection.objects.filter(config_folder=config_folder).update(**{field: new_value})
            messages.success(request, f"Successfully updated {field} of {config_folder}.")
        else:
            messages.error(
                request,
                f"Can't update empty value from GitHub: {field} of {config_folder}.",
            )

        return redirect("sde_collections:consolidate_db_and_github_configs")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["differences"] = self.data

        return context


class ResolvedTitleListView(ListView):
    model = DeltaResolvedTitle
    context_object_name = "resolved_titles"


class ResolvedTitleErrorListView(ListView):
    model = DeltaResolvedTitleError
    context_object_name = "resolved_title_errors"


class TitlesAndErrorsView(View):
    def get(self, request, *args, **kwargs):
        resolved_titles = DeltaResolvedTitle.objects.select_related("title_pattern", "delta_url").all()
        resolved_title_errors = DeltaResolvedTitleError.objects.select_related("title_pattern", "delta_url").all()
        context = {
            "resolved_titles": resolved_titles,
            "resolved_title_errors": resolved_title_errors,
        }
        return render(request, "sde_collections/titles_and_errors_list.html", context)
