import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { AppSettings, SlackSettings, ResendSettings, EmailTemplate } from "@/types";
import { showSuccess, showError } from "@/utils/toast";

// Query keys
export const settingsKeys = {
  all: ['settings'] as const,
  app: () => [...settingsKeys.all, 'app'] as const,
  slack: () => [...settingsKeys.all, 'slack'] as const,
  slackChannels: () => [...settingsKeys.all, 'slack', 'channels'] as const,
  resend: () => [...settingsKeys.all, 'resend'] as const,
  emailTemplates: () => [...settingsKeys.all, 'email', 'templates'] as const,
};

// Get app settings
export const useAppSettings = () => {
  return useQuery({
    queryKey: settingsKeys.app(),
    queryFn: () => api.getSettings(),
    select: (data) => data.data,
  });
};

// Update app settings
export const useUpdateAppSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: Partial<AppSettings>) => api.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.app() });
      showSuccess("Settings updated successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to update settings");
    },
  });
};

// Get Slack settings
export const useSlackSettings = () => {
  return useQuery({
    queryKey: settingsKeys.slack(),
    queryFn: () => api.getSlackSettings(),
    select: (data) => data.data,
  });
};

// Update Slack settings
export const useUpdateSlackSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: SlackSettings) => api.updateSlackSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.slack() });
      showSuccess("Slack settings updated successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to update Slack settings");
    },
  });
};

// Test Slack connection
export const useTestSlackConnection = () => {
  return useMutation({
    mutationFn: (channelId: string) => api.testSlackConnection(channelId),
    onSuccess: (response) => {
      if (response.data.success) {
        showSuccess(response.data.message || "Slack connection successful");
      } else {
        showError(response.data.message || "Slack connection failed");
      }
    },
    onError: (error: any) => {
      showError(error.message || "Failed to test Slack connection");
    },
  });
};

// Get Slack channels
export const useSlackChannels = () => {
  return useQuery({
    queryKey: settingsKeys.slackChannels(),
    queryFn: () => api.getSlackChannels(),
    select: (data) => data.data,
  });
};

// Get Resend settings
export const useResendSettings = () => {
  return useQuery({
    queryKey: settingsKeys.resend(),
    queryFn: () => api.getResendSettings(),
    select: (data) => data.data,
  });
};

// Update Resend settings
export const useUpdateResendSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: ResendSettings) => api.updateResendSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.resend() });
      showSuccess("Resend settings updated successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to update Resend settings");
    },
  });
};

// Test Resend configuration
export const useTestResendConfiguration = () => {
  return useMutation({
    mutationFn: () => api.testResendConfiguration(),
    onSuccess: (response) => {
      if (response.data.success) {
        showSuccess(response.data.message || "Resend configuration is valid");
      } else {
        showError(response.data.message || "Resend configuration failed");
      }
    },
    onError: (error: any) => {
      showError(error.message || "Failed to test Resend configuration");
    },
  });
};

// Get email templates
export const useEmailTemplates = () => {
  return useQuery({
    queryKey: settingsKeys.emailTemplates(),
    queryFn: () => api.getEmailTemplates(),
    select: (data) => data.data,
  });
};

// Update email template
export const useUpdateEmailTemplate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ templateId, template }: { templateId: string; template: EmailTemplate }) =>
      api.updateEmailTemplate(templateId, template),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.emailTemplates() });
      showSuccess("Email template updated successfully");
    },
    onError: (error: any) => {
      showError(error.message || "Failed to update email template");
    },
  });
};

// Send test email
export const useSendTestEmail = () => {
  return useMutation({
    mutationFn: ({ templateId, recipientEmail }: { templateId: string; recipientEmail: string }) =>
      api.sendTestEmail(templateId, recipientEmail),
    onSuccess: (response) => {
      if (response.data.success) {
        showSuccess(response.data.message || "Test email sent successfully");
      } else {
        showError(response.data.message || "Failed to send test email");
      }
    },
    onError: (error: any) => {
      showError(error.message || "Failed to send test email");
    },
  });
};