#!/usr/bin/env ruby
require 'open-uri'
require 'rss'
require 'yaml'
require 'time'
require 'fileutils'

FEEDS_FILE = File.expand_path('../events/feeds.txt', __dir__)
OUT_FILE   = File.expand_path('../_data/other_events.yml', __dir__)

feeds = File.read(FEEDS_FILE).lines.map(&:strip).reject { |l| l.empty? || l.start_with?('#') }

events = []

feeds.each do |url|
  begin
    URI.open(url, open_timeout: 10, read_timeout: 10) do |io|
      feed = RSS::Parser.parse(io.read, false)
      source = feed.respond_to?(:channel) ? feed.channel.title : (feed.title rescue url)
      (feed.items || []).each do |item|
        date = item.respond_to?(:pubDate) ? item.pubDate : (item.respond_to?(:date) ? item.date : nil)
        events << {
          'title'       => (item.title || 'Untitled').to_s,
          'url'         => (item.link || (item.guid && item.guid.content) || '').to_s,
          'date'        => (date ? (date.respond_to?(:iso8601) ? date.iso8601 : date.to_s) : nil),
          'description' => (item.description || item.content || '').to_s,
          'source'      => source.to_s
        }
      end
    end
  rescue => e
    warn "Failed to fetch #{url}: #{e.message}"
  end
end

events.sort_by! do |ev|
  begin
    Time.parse(ev['date'].to_s)
  rescue
    Time.at(0)
  end
end.reverse!

# ensure output directory exists
FileUtils.mkdir_p(File.dirname(OUT_FILE))

File.write(OUT_FILE, events.to_yaml)
puts "Wrote #{events.size} items to #{OUT_FILE}"