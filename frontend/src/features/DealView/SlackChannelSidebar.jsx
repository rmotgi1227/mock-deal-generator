import React from 'react';
import { Hash } from 'lucide-react';
export default function SlackChannelSidebar({ channels, selectedChannelId, onSelectChannel }) {
  return (<div className="w-64 bg-slate-900 text-white border-r border-slate-700 overflow-y-auto">
    <div className="px-4 py-3 border-b border-slate-700"><h3 className="font-bold text-sm">Deal Slack</h3></div>
    <div className="py-2">{channels.map(ch => (<button key={ch.channel_id} onClick={() => onSelectChannel(ch.channel_id)} className={`w-full text-left px-4 py-2 flex items-center gap-2 hover:bg-slate-800 ${selectedChannelId === ch.channel_id ? 'bg-slate-700' : ''}`}><Hash size={16} /><span className="text-sm">{ch.name}</span></button>))}</div>
    {selectedChannelId && <div className="border-t border-slate-700 p-4 text-xs text-slate-400"><p className="font-semibold text-white mb-1">Topic</p><p>{channels.find(ch => ch.channel_id === selectedChannelId)?.topic}</p></div>}
  </div>);
}
