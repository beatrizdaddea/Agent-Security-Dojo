from app.tools.runtime import ToolRuntime


def read_document(runtime: ToolRuntime, document_name: str):
    return runtime.call("read_document", document_name=document_name)


def search_drive(runtime: ToolRuntime, query: str):
    return runtime.call("search_drive", query=query)


def delete_document(runtime: ToolRuntime, document_name: str, source: str = "agent"):
    return runtime.call("delete_document", source=source, document_name=document_name)

