Feature: Cite Managments
  
  Scenario: Reschedule Cite
    Given There is a cite assigned
    When user changes date or hour
    Then System updates cite information