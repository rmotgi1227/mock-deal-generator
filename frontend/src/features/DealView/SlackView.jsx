import React, { useState, useMemo } from 'react';
import SlackChannelSidebar from './SlackChannelSidebar';
import SlackMessageThread from './SlackMessageThread';
export default function SlackView({ deal }) {
  const channels = useMemo(() => (deal.timeline_events || []).filter(e => e.record_type === 'slack_channel').map(e => e.channel).filter(Boolean), [deal.timeline_events]);
  const [selectedChannelId, setSelectedChannelId] = useState(channels[0]?.channel_id || null);
  const selectedChannel = channels.find(ch => ch.channel_id === selectedChannelId);
  if (channels.length === 0) return <div className="flex items-center justify-center h-96 text-gray-500">No Slack channels</div>;
  return (<div className="flex h-full bg-white rounded-lg border border-gray-200 overflow-hidden">
    <SlackChannelSidebar channels={channels} selectedChannelId={selectedChannelId} onSelectChannel={setSelectedChannelId} />
    <SlackMessageThread channel={selectedChannel} />
  </div>);
}
