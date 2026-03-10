"""Форматирование данных об авторах."""


def format_authors_display(authors: list) -> str:
    """
    Собрать строку для отображения списка авторов (имя через запятую).
    Принимает итерабельность объектов с атрибутом name (например, Author).
    """
    if not authors:
        return ""
    return ", ".join(getattr(a, "name", str(a)) for a in authors)
