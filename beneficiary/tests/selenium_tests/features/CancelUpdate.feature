Feature: Update Personal Beneficiary data
  
  Scenario: Cancel modifications
    Given Secretariat it's making changes to beneficiary
    When click in "Cancel"
    Then System don't make modifications to beneficiary