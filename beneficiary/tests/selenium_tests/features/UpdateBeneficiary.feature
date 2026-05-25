Feature: Update Personal Beneficiary data
  
  Scenario: Successful data Update
    Given Secretariat access to beneficiary profile
    When makes one or more personal data modifications
    And click in "Save Changes"
    Then System Update beneficiary information
    And is recording in binnacle