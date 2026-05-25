Feature: Beneficiary Register
  
  Scenario: Successful Beneficiary register
    Given Secretariat access to register form
    When enters name, document, direction, phone, mail, agreement with private policts and document file
    And click in "Register"
    Then System save Beneficiary record