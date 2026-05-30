Feature: Metricas de canales de comunicacion (HU-24)

  Scenario: Administrador ve la pagina de metricas
    Given El administrador inicia sesion
    When Ingresa a la pagina de metricas de comunicacion
    Then Ve las tarjetas de conteo por canal
    And Ve la tabla de interacciones

  Scenario: Filtrar interacciones por canal especifico
    Given El administrador esta en la pagina de metricas
    When Selecciona el tipo de canal "llamada" y aplica el filtro
    Then La tabla solo muestra interacciones de tipo Llamada

  Scenario: Limpiar filtro muestra todas las interacciones
    Given El administrador filtro por un canal especifico
    When Hace clic en Limpiar
    Then La tabla muestra todas las interacciones sin filtro

  Scenario: Secretaria no puede acceder a metricas
    Given La secretaria inicia sesion
    When Intenta acceder a la pagina de metricas de comunicacion
    Then Es redirigida o recibe acceso denegado
