Feature: Cite Managment
  
  Scenario: Cancel Cite
    Given There is a cite assigned previously
    When user selects cancel cite
    Then System update cite state to "Cancelada"