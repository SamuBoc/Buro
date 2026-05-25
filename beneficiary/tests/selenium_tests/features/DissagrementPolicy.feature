Feature: Authorization policy personal data treatment
  
  Scenario: Dissagrement Authorization
    Given register form beneficiary that have agreement policy
    When registered all the info and don't mark Authorization option
    And click in "Register" to send form without Authorization
    Then System shows a message that explain Authorization is necessary