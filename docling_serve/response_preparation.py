import asyncio
import logging

from fastapi import BackgroundTasks, Response

from docling_jobkit.datamodel.result import (
    ChunkedDocumentResult,
    DoclingTaskResult,
    ExportResult,
    RemoteTargetResult,
    ZipArchiveResult,
)
from docling_jobkit.orchestrators.base_orchestrator import (
    BaseOrchestrator,
)

from docling_serve.datamodel.responses import (
    ChunkDocumentResponse,
    ConvertDocumentResponse,
    PresignedUrlConvertDocumentResponse,
)
from docling_serve.markdown_cleanup import (
    MarkdownCleanupOptions,
    cleanup_markdown,
)
from docling_serve.settings import docling_serve_settings

_log = logging.getLogger(__name__)


async def prepare_response(
    task_id: str,
    task_result: DoclingTaskResult,
    orchestrator: BaseOrchestrator,
    background_tasks: BackgroundTasks,
):
    response: (
        Response
        | ConvertDocumentResponse
        | PresignedUrlConvertDocumentResponse
        | ChunkDocumentResponse
    )
    if isinstance(task_result.result, ExportResult):
        document = task_result.result.content

        if (
            docling_serve_settings.markdown_cleanup_enabled
            and getattr(document, "md_content", None)
        ):
            cleanup_options = MarkdownCleanupOptions(
                remove_patterns=docling_serve_settings.markdown_cleanup_remove_patterns,
                auto_remove_domain_headings=docling_serve_settings.markdown_cleanup_auto_remove_domains,
                combine_numbered_headings=docling_serve_settings.markdown_cleanup_combine_headings,
                reflow_paragraphs=docling_serve_settings.markdown_cleanup_reflow_paragraphs,
            )

            cleaned_md = cleanup_markdown(document.md_content, cleanup_options)
            if cleaned_md != document.md_content:
                if hasattr(document, "model_copy"):
                    document = document.model_copy(update={"md_content": cleaned_md})
                else:
                    document.md_content = cleaned_md

        response = ConvertDocumentResponse(
            document=document,
            status=task_result.result.status,
            processing_time=task_result.processing_time,
            timings=task_result.result.timings,
            errors=task_result.result.errors,
        )
    elif isinstance(task_result.result, ZipArchiveResult):
        response = Response(
            content=task_result.result.content,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="converted_docs.zip"'
            },
        )
    elif isinstance(task_result.result, RemoteTargetResult):
        response = PresignedUrlConvertDocumentResponse(
            processing_time=task_result.processing_time,
            num_converted=task_result.num_converted,
            num_succeeded=task_result.num_succeeded,
            num_failed=task_result.num_failed,
        )
    elif isinstance(task_result.result, ChunkedDocumentResult):
        response = ChunkDocumentResponse(
            chunks=task_result.result.chunks,
            documents=task_result.result.documents,
            processing_time=task_result.processing_time,
        )
    else:
        raise ValueError("Unknown result type")

    if docling_serve_settings.single_use_results:

        async def _remove_task_impl():
            await asyncio.sleep(docling_serve_settings.result_removal_delay)
            await orchestrator.delete_task(task_id=task_id)

        async def _remove_task():
            asyncio.create_task(_remove_task_impl())  # noqa: RUF006

        background_tasks.add_task(_remove_task)

    return response
