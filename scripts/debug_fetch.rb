#!/usr/bin/env ruby
require 'open-uri'
require 'rss'
require 'time'

FEEDS = File.join(__dir__, '..', 'events', 'feeds.txt')
unless File.exist?(FEEDS)
  warn "Feeds file not found: #{FEEDS}"
  exit 1
end

File.read(FEEDS).lines.map(&:strip).reject { |l| l.empty? || l.start_with?('#') }.each do |url|
  puts "=== URL: #{url}"
  begin
    URI.open(url, "User-Agent" => "MishMashFetcher/1.0", open_timeout: 10, read_timeout: 10) do |io|
      status = io.respond_to?(:status) ? io.status.join(',') : 'unknown'
      ctype  = (io.respond_to?(:meta) && io.meta['content-type']) || io.content_type rescue 'unknown'
      puts "HTTP: status=#{status} content_type=#{ctype}"
      text = io.read
      feed = nil
      begin
        feed = RSS::Parser.parse(text, false)
      rescue => e
        puts "RSS::Parser.parse failed: #{e.class}: #{e.message}"
      end
      if feed.nil?
        puts "Parser returned nil — first 400 chars of response:"
        puts text[0..400].gsub(/\s+/, ' ')
        next
      end
      items = feed.respond_to?(:items) ? feed.items : []
      puts "Found #{items.size} items"
      if items.any?
        first = items.first
        puts "First item title: #{first.title.inspect}"
        puts "First item link:  #{(first.link || (first.respond_to?(:guid) && first.guid.content) || 'n/a')}"
        puts "First item date:  #{(first.respond_to?(:pubDate) ? first.pubDate : (first.respond_to?(:date) ? first.date : 'n/a'))}"
      end
    end
  rescue => e
    puts "Fetch error: #{e.class}: #{e.message}"
    puts e.backtrace.first(5)
  end
  puts
end