from behave import given, when, then
from selenium.webdriver.common.by import By
from pages.login_page import LoginPage
from pages.metrics_page import MetricsPage

ADMIN_USER = "admin_selenium"
ADMIN_PASS = "selenium123"
SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"


@given('El administrador esta en la pagina de metricas')
def step_admin_on_metrics(context):
    context.login_page = LoginPage(context.driver)
    context.metrics_page = MetricsPage(context.driver)
    context.login_page.login(ADMIN_USER, ADMIN_PASS)
    context.metrics_page.go_to_metrics()


@when('Ingresa a la pagina de metricas de comunicacion')
def step_go_to_metrics(context):
    context.metrics_page = MetricsPage(context.driver)
    context.metrics_page.go_to_metrics()


@then('Ve las tarjetas de conteo por canal')
def step_see_metric_cards(context):
    # Total card is always rendered; check the page loaded and container is present
    counts = context.metrics_page.get_metric_counts()
    assert len(counts) >= 1, \
        "No se encontró ninguna tarjeta de métricas (ni la tarjeta Total)"


@then('Ve la tabla de interacciones')
def step_see_interactions_table(context):
    assert context.metrics_page.is_element_present(context.metrics_page.TABLE_ROWS), \
        "No se encontró la tabla de interacciones"


@when('Selecciona el tipo de canal "llamada" y aplica el filtro')
def step_filter_by_call(context):
    context.metrics_page.filter_by_type('llamada')


@then('La tabla solo muestra interacciones de tipo Llamada')
def step_only_calls_visible(context):
    labels = context.metrics_page.get_visible_channel_labels()
    for label in labels:
        assert 'Llamada' in label, \
            f"Se encontró interacción de otro tipo: {label}"


@given('El administrador filtro por un canal especifico')
def step_admin_filtered(context):
    context.login_page = LoginPage(context.driver)
    context.metrics_page = MetricsPage(context.driver)
    context.login_page.login(ADMIN_USER, ADMIN_PASS)
    context.metrics_page.go_to_metrics()
    context.metrics_page.filter_by_type('llamada')


@when('Hace clic en Limpiar')
def step_clear_filter(context):
    context.metrics_page.clear_filter()


@then('La tabla muestra todas las interacciones sin filtro')
def step_all_visible(context):
    url = context.metrics_page.get_current_url()
    assert 'tipo=' not in url, \
        "La URL todavía tiene parámetro de filtro después de limpiar"


@when('Intenta acceder a la pagina de metricas de comunicacion')
def step_sec_go_to_metrics(context):
    context.metrics_page = MetricsPage(context.driver)
    context.metrics_page.go_to_metrics()


@then('Es redirigida o recibe acceso denegado')
def step_metrics_access_denied(context):
    from pages.base_page import BASE_URL
    url = context.metrics_page.get_current_url()
    metrics_path = f"{BASE_URL}/casos/metricas/comunicaciones/"
    # The secretaria should NOT be on the metrics page (any redirect counts as blocked)
    assert not url.startswith(metrics_path), \
        f"La secretaria accedió a métricas cuando no debería. URL: {url}"
