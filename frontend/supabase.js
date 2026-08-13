import { createClient } from '@supabase/supabase-js';

let client;

export function initialize(url, publishableKey, options = {}) {
  if (!url || !publishableKey) {
    throw new Error('Supabase public configuration is missing');
  }
  if (!client) {
    client = createClient(url, publishableKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
        detectSessionInUrl: false,
      },
      realtime: {
        params: { eventsPerSecond: 10 },
      },
      ...options,
    });
  }
  return client;
}

export function getClient() {
  if (!client) {
    throw new Error('Supabase client has not been initialized');
  }
  return client;
}

export async function connectPrivateChannel(topic, handlers = {}, presence = {}) {
  const response = await fetch('/auth/realtime-session', {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error('Realtime authentication failed');
  }
  const config = await response.json();
  const supabase = initialize(config.url, config.publishable_key);
  await supabase.realtime.setAuth(config.access_token);

  const channel = supabase.channel(topic, {
    config: {
      private: true,
      broadcast: { self: false, ack: true },
      presence: { key: String(config.user_id) },
    },
  });
  Object.entries(handlers).forEach(([event, callback]) => {
    channel.on('broadcast', { event }, ({ payload }) => callback(payload));
  });
  if (presence.onSync) {
    channel.on('presence', { event: 'sync' }, () => {
      presence.onSync(channel.presenceState());
    });
  }
  channel.subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({
        user_id: config.user_id,
        username: config.username,
        online_at: new Date().toISOString(),
      });
    }
    if (presence.onStatus) presence.onStatus(status);
  });
  return channel;
}
