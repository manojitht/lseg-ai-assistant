# SOP-001: Access Management
Version: 1.0
Classification: Confidential
Last Updated: 2024-01-10

## VPN Access Issues

If a user encounters VPN access errors:
1. Verify VPN credentials
2. Check MFA token validity
3. If MFA token is LOST:
   - Remote reset is strictly prohibited
   - User must visit a regional hub in person
4. Assign ticket to Security-Ops if unresolved

## MFA Reset Policy

Remote MFA resets:
- Not allowed under any circumstances
- No exceptions via phone or video call

## Exception Handling

In rare cases, the CISO may authorise a remote MFA reset.
This override must:
- Be logged
- Be linked to a specific incident ID
- Require biometric verification

This exception was used once:
- Incident ID: TKT-7421

## Account Lockout

If account is locked:
1. Verify identity
2. Reset password
3. Re-enable access within 15 minutes
4. Notify user

