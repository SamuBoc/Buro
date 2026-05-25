Feature: Authorization policy personal data treatment
  
  Scenario: Agreement Authorization
    Given Secretariat access to register form beneficiary that have agreement policy
    When registered all the info and mark Authorization option
    And click in "Register" to send form
    Then System allows make the register