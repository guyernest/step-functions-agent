import { defineAuth } from '@aws-amplify/backend';

/**
 * Define and configure your auth resource
 * @see https://docs.amplify.aws/gen2/build-a-backend/auth
 */
export const auth = defineAuth({
  name: 'StepFunctionsAgentAuth',
  loginWith: {
    email: true,
  },
  groups: ['Admins', 'Users'],
  userAttributes: {
    preferredUsername: {
      required: false,
      mutable: true,
    },
  },
  accountRecovery: 'EMAIL_ONLY',
  multifactor: {
    mode: 'OPTIONAL',
    totp: true,
  },
});
