#!/usr/bin/env ruby
require 'open-uri'
require 'rss'
require 'yaml'
require 'time'
require 'fileutils'

ROOT = File.expand_path('..', __dir__)
FEEDS_FILE = File.join(ROOT, 'events', 'feeds.txt')
OUT_DIR = File.join(ROOT, '_data')
OUT_FILE = File.join(OUT_DIR, 'other_events.yml')

unless File.exist?(FEEDS_FILE)
  warn "Feeds file not found: #{FEEDS_FILE}"
  exit 1
end

feeds = File.read(FEEDS_FILE).lines.map(&:strip).reject { |l| l.empty? || l.start_with?('#') }

events = []

feeds.each do |url|
  begin
    URI.open(url, "User-Agent" => "MishMashFetcher/1.0", open_timeout: 10, read_timeout: 10) do |io|
      text = io.read
      feed = RSS::Parser.parse(text, false) rescue nil
      unless feed
        warn "Failed to parse feed: #{url}"
        next
      end

      # Support both RSS (feed.items) and Atom (feed.entries)
      items = if feed.respond_to?(:items) && feed.items && !feed.items.empty?
                feed.items
              elsif feed.respond_to?(:entries) && feed.entries
                feed.entries
              else
                []
              end

      source = if feed.respond_to?(:channel) && feed.channel.respond_to?(:title)
                 feed.channel.title.to_s
               elsif feed.respond_to?(:title)
                 (feed.title.respond_to?(:content) ? feed.title.content : feed.title).to_s
               else
                 url
               end

      items.each do |item|
        # title
        title = if item.respond_to?(:title)
                  t = item.title
                  t.respond_to?(:content) ? t.content.to_s : t.to_s
                else
                  'Untitled'
                end

        # link (handle Atom and RSS variations)
        link = nil
        if item.respond_to?(:link) && item.link
          if item.link.is_a?(Array)
            l = item.link.find { |ll| ll.respond_to?(:href) } || item.link.first
            link = l.respond_to?(:href) ? l.href : (l.respond_to?(:content) ? l.content : l.to_s)
          else
            l = item.link
            link = l.respond_to?(:href) ? l.href : (l.respond_to?(:content) ? l.content : l.to_s)
          end
        elsif item.respond_to?(:links) && item.links.is_a?(Array)
          l = item.links.find { |ll| ll.respond_to?(:href) } || item.links.first
          link = l.respond_to?(:href) ? l.href : l.to_s
        elsif item.respond_to?(:guid) && item.guid.respond_to?(:content)
          link = item.guid.content.to_s
        end
        link ||= url

        # date (try common fields)
        date = if item.respond_to?(:pubDate) && item.pubDate
                 item.pubDate
               elsif item.respond_to?(:date) && item.date
                 item.date
               elsif item.respond_to?(:updated) && item.updated
                 item.updated
               elsif item.respond_to?(:published) && item.published
                 item.published
               else
                 nil
               end
        date_iso = date ? (date.respond_to?(:iso8601) ? date.iso8601 : date.to_s) : nil

        # description / summary / content
        description = if item.respond_to?(:description) && item.description
                        item.description.to_s
                      elsif item.respond_to?(:summary) && item.summary
                        item.summary.to_s
                      elsif item.respond_to?(:content) && item.content
                        # Atom content may be an object
                        c = item.content
                        c.respond_to?(:content) ? c.content.to_s : c.to_s
                      else
                        ''
                      end

        events << {
          'title'       => title,
          'url'         => link,
          'date'        => date_iso,
          'description' => description,
          'source'      => source
        }
      end
    end
  rescue => e
    warn "Failed to fetch #{url}: #{e.class}: #{e.message}"
  end
end

events.sort_by! do |ev|
  begin
    Time.parse(ev['date'].to_s)
  rescue
    Time.at(0)
  end
end.reverse!

FileUtils.mkdir_p(File.dirname(OUT_FILE))
File.write(OUT_FILE, events.to_yaml)
puts "Wrote #{events.size} items to #{OUT_FILE}"