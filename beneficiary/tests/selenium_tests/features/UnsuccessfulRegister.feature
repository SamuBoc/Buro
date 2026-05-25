Feature: Beneficiary Register
  
  Scenario: Incomplet fields
    Given Secretariat access to register form beneficiary
    When try registering a beneficiary without all the fields completed
    And click in "Register" with empty fields
    Then System shows a message explaining that all the fields are necessary