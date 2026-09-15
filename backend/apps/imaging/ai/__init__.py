def get_provider(name: str):
    if name == "openai":
        from .openai_provider import OpenAIRecreateProvider

        return OpenAIRecreateProvider()
    from .noop import NoopRecreateProvider

    return NoopRecreateProvider()
