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
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CollectionGithubIssueForm, CommentsForm, RequiredUrlForm
from .models.candidate_url import CandidateURL, ResolvedTitle, ResolvedTitleError
from .models.collection import Collection, Comments, RequiredUrls, WorkflowHistory
from .models.collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    WorkflowStatusChoices,
)
from .models.pattern import (
    DivisionPattern,
    DocumentTypePattern,
    ExcludePattern,
    IncludePattern,
    TitlePattern,
)
from .serializers import (
    CandidateURLAPISerializer,
    CandidateURLBulkCreateSerializer,
    CandidateURLSerializer,
    AffectedURLSerializer,
    CollectionReadSerializer,
    CollectionSerializer,
    DivisionPatternSerializer,
    DocumentTypePatternSerializer,
    ExcludePatternSerializer,
    IncludePatternSerializer,
    TitlePatternSerializer,
)
from .tasks import push_to_github_task
from .utils.health_check import generate_db_github_metadata_differences

User = get_user_model()


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
            .annotate(num_candidate_urls=models.Count("candidate_urls"))
            .order_by("-num_candidate_urls")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = "collections"
        context["curators"] = User.objects.filter(groups__name="Curators")
        context["curation_status_choices"] = CurationStatusChoices
        context["workflow_status_choices"] = WorkflowStatusChoices

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

        return context


class RequiredUrlsDeleteView(LoginRequiredMixin, DeleteView):
    model = RequiredUrls

    def get_success_url(self, *args, **kwargs):
        return reverse("sde_collections:detail", kwargs={"pk": self.object.collection.pk})


class CandidateURLsListView(LoginRequiredMixin, ListView):
    """
    Display a list of collections in the system
    """

    model = CandidateURL
    template_name = "sde_collections/candidate_urls_list.html"
    context_object_name = "candidate_urls"
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
        context["segment"] = "candidate-url-list"
        context["collection"] = self.collection
        context["regex_exclude_patterns"] = self.collection.excludepattern.filter(
            match_pattern_type=2
        )  # 2=regex patterns
        context["title_patterns"] = self.collection.titlepattern.all()
        context["workflow_status_choices"] = WorkflowStatusChoices
        context["is_multi_division"] = self.collection.is_multi_division

        return context


class BaseAffectedURLsListView(LoginRequiredMixin, ListView):
    """
    Base view for displaying a list of URLs affected by a match pattern
    """

    model = CandidateURL
    template_name = "sde_collections/affected_urls.html"
    context_object_name = "affected_urls"
    pattern_model = None
    pattern_type = None

    def get_queryset(self):
        self.pattern = self.pattern_model.objects.get(id=self.kwargs["id"])
        queryset = self.pattern.matched_urls()
        # print(list(queryset))
        for url in queryset:
            print(url.id)
        return self.pattern.matched_urls()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pattern"] = self.pattern
        context["pattern_id"] = self.kwargs["id"]
        print(context["pattern_id"])
        context["url_count"] = self.get_queryset().count()
        context["collection"] = self.pattern.collection
        context["pattern_type"] = self.pattern_type
        return context


class ExcludePatternAffectedURLsListView(BaseAffectedURLsListView):
    pattern_model = ExcludePattern
    pattern_type = "Exclude"

    def get_queryset(self):
        self.pattern = self.pattern_model.objects.get(id=self.kwargs["id"])
        queryset = self.pattern.matched_urls()
        
        # Subquery to get the match_pattern and id of the IncludePattern
        include_pattern_subquery = IncludePattern.objects.filter(
            candidate_urls=models.OuterRef("pk")
        ).values('match_pattern', 'id')[:1]

        # Annotate with inclusion status, match_pattern, and id of the IncludePattern
        queryset = queryset.annotate(
            included=models.Exists(include_pattern_subquery),
            included_by_pattern=models.Subquery(
                include_pattern_subquery.values('match_pattern'),
                output_field=models.CharField()
            ),
            match_pattern_id=models.Subquery(
                include_pattern_subquery.values('id'),
                output_field=models.IntegerField()
            )
        )
        
        return queryset


class IncludePatternAffectedURLsListView(BaseAffectedURLsListView):
    pattern_model = IncludePattern
    pattern_type = "Include"


class TitlePatternAffectedURLsListView(BaseAffectedURLsListView):
    pattern_model = TitlePattern
    pattern_type = "Title"


class DocumentTypePatternAffectedURLsListView(BaseAffectedURLsListView):
    pattern_model = DocumentTypePattern
    pattern_type = "Document Type"


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


class CandidateURLViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLSerializer

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
        candidate_url = get_object_or_404(CandidateURL, pk=pk)
        division = request.data.get("division")
        if division:
            candidate_url.division = division
            candidate_url.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Division is required."})


class CandidateURLBulkCreateView(generics.ListCreateAPIView):
    queryset = CandidateURL.objects.all()
    serializer_class = CandidateURLBulkCreateSerializer

    def perform_create(self, serializer, collection_id=None):
        for validated_data in serializer.validated_data:
            validated_data["collection_id"] = collection_id
        super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        collection = Collection.objects.get(config_folder=config_folder)
        collection.candidate_urls.all().delete()

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, collection_id=collection.pk)

        collection.apply_all_patterns()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CandidateURLAPIView(ListAPIView):
    serializer_class = CandidateURLAPISerializer

    def get(self, request, *args, **kwargs):
        config_folder = kwargs.get("config_folder")
        self.config_folder = config_folder
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            CandidateURL.objects.filter(collection__config_folder=self.config_folder)
            .with_exclusion_and_inclusion_status()
            .filter(models.Q(excluded=False) | models.Q(included=True))
        )
        return queryset


class ExcludePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = ExcludePattern.objects.all()
    serializer_class = ExcludePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        match_pattern = request.POST.get("match_pattern")
        collection_id = request.POST.get("collection")
        try:
            ExcludePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except ExcludePattern.DoesNotExist:
            return super().create(request, *args, **kwargs)


class IncludePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = IncludePattern.objects.all()
    serializer_class = IncludePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        match_pattern = request.POST.get("match_pattern")
        collection_id = request.POST.get("collection")
        try:
            IncludePattern.objects.get(
                collection_id=Collection.objects.get(id=collection_id),
                match_pattern=match_pattern,
            ).delete()
            return Response(status=status.HTTP_200_OK)
        except IncludePattern.DoesNotExist:
            return super().create(request, *args, **kwargs)


class TitlePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = TitlePattern.objects.all()
    serializer_class = TitlePatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")


class DocumentTypePatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DocumentTypePattern.objects.all()
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
                DocumentTypePattern.objects.get(
                    collection_id=Collection.objects.get(id=collection_id),
                    match_pattern=match_pattern,
                    match_pattern_type=DocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
                ).delete()
                return Response(status=status.HTTP_200_OK)
            except DocumentTypePattern.DoesNotExist:
                return Response(status=status.HTTP_204_NO_CONTENT)


class DivisionPatternViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = DivisionPattern.objects.all()
    serializer_class = DivisionPatternSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("match_pattern")

    def create(self, request, *args, **kwargs):
        division = request.POST.get("division")
        if division:
            return super().create(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Division is required."})


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
    model = ResolvedTitle
    context_object_name = "resolved_titles"


class ResolvedTitleErrorListView(ListView):
    model = ResolvedTitleError
    context_object_name = "resolved_title_errors"


class TitlesAndErrorsView(View):
    def get(self, request, *args, **kwargs):
        resolved_titles = ResolvedTitle.objects.select_related("title_pattern", "candidate_url").all()
        resolved_title_errors = ResolvedTitleError.objects.select_related("title_pattern", "candidate_url").all()
        context = {
            "resolved_titles": resolved_titles,
            "resolved_title_errors": resolved_title_errors,
        }
        return render(request, "sde_collections/titles_and_errors_list.html", context)


class BaseAffectedURLsViewSet(CollectionFilterMixin, viewsets.ModelViewSet):
    queryset = CandidateURL.objects.all()
    serializer_class = AffectedURLSerializer
    pattern_model = None
    pattern_type = None

    def get_queryset(self):
        # queryset = super().get_queryset()
        pattern_id = self.request.GET.get("pattern_id")
        self.pattern = self.pattern_model.objects.get(id=pattern_id)
        queryset = self.pattern.matched_urls()
        print("The length is ", len(queryset))
        return queryset
    
class IncludePatternAffectedURLsViewSet(BaseAffectedURLsViewSet):
    pattern_model = IncludePattern
    pattern_type = "Include"

class ExcludePatternAffectedURLsViewSet(BaseAffectedURLsViewSet):
    pattern_model = ExcludePattern
    pattern_type = "Exclude"
    
    def get_queryset(self):
        pattern_id = self.request.GET.get("pattern_id")
        self.pattern = self.pattern_model.objects.get(id=pattern_id)
        queryset = self.pattern.matched_urls()
        
        # Subquery to get the match_pattern and id of the IncludePattern
        include_pattern_subquery = IncludePattern.objects.filter(
            candidate_urls=models.OuterRef("pk")
        ).values('match_pattern', 'id')[:1]

        # Annotate with inclusion status, match_pattern, and id of the IncludePattern
        queryset = queryset.annotate(
            included=models.Exists(include_pattern_subquery),
            included_by_pattern=models.Subquery(
                include_pattern_subquery.values('match_pattern'),
                output_field=models.CharField()
            ),
            match_pattern_id=models.Subquery(
                include_pattern_subquery.values('id'),
                output_field=models.IntegerField()
            )
        )
        
        return queryset

    
class TitlePatternAffectedURLsViewSet(BaseAffectedURLsViewSet):
    pattern_model = TitlePattern
    pattern_type = "Title"
    
class DocumentTypePatternAffectedURLsViewSet(BaseAffectedURLsViewSet):
    pattern_model = DocumentTypePattern
    pattern_type = "Document Type"
