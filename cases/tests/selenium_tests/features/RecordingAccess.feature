Feature: Acceso controlado a grabaciones de llamadas (HU-23)

  Scenario: Administrador ve reproductor de audio en detalle del caso
    Given El administrador inicia sesion
    When Ingresa al detalle del caso con grabacion
    Then Ve el reproductor de audio en el historial de interacciones

  Scenario: Secretaria ve candado en lugar del reproductor
    Given La secretaria inicia sesion
    When Ingresa al detalle del caso con grabacion
    Then Ve el icono de candado en lugar del reproductor

  Scenario: Secretaria no puede acceder a la URL de grabacion directamente
    Given La secretaria inicia sesion
    When Intenta acceder a la URL de la grabacion directamente
    Then La secretaria es redirigida o recibe acceso denegado a la grabacion
