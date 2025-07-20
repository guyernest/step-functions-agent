# Secret Deletion Record

## Deleted Secret Details

- **Secret Name**: `/ai-agent/MicrosoftGraphAPISecrets`
- **ARN**: `arn:aws:secretsmanager:eu-west-1:145023107515:secret:/ai-agent/MicrosoftGraphAPISecrets-PJwMZ3`
- **AWS Profile**: CGI-PoC
- **Region**: eu-west-1
- **Deletion Date**: 2025-07-20T14:25:14.563000-07:00
- **Deletion Type**: Immediate (force delete without recovery)

## Command Used

```bash
aws secretsmanager delete-secret \
  --secret-id "/ai-agent/MicrosoftGraphAPISecrets" \
  --force-delete-without-recovery \
  --profile CGI-PoC \
  --region eu-west-1
```

## Notes

- The secret was permanently deleted without any recovery window
- This action cannot be undone
- The secret was part of the AI Agent framework's Microsoft Graph integration
