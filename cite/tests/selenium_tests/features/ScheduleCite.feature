Feature: Cite Managment

  Scenario: Schedule Cite
    Given Secretariat goes to cite module
    When Select an avaible date and hour
    And Confirm schedule
    Then System register a new cite