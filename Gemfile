source 'http://rubygems.org'

gem 'rake', '~> 11.2.2'
gem 'nokogiri', '~> 1.6', '<= 1.6.8.1'

# Specify the JSON dependency so that rubocop and other gem do not try to install it
gem 'json', '~> 1.8'

gem 'colored', '~> 1.2'

if RUBY_PLATFORM =~ /win32/
  gem 'win32console', '~> 1.3.2', platform: [:mswin, :mingw]
end

group :test do
  gem 'minitest', '~> 5.9'
  gem 'rubocop', '~> 0.49.0'
  gem 'rubocop-checkstyle_formatter', '~> 0.1.1'
  gem 'ci_reporter_minitest', '~> 1.0.0'
  gem 'simplecov'
  gem 'codecov'
  gem 'minitest-reporters'
  gem 'minitest-ci', :git => 'https://github.com/circleci/minitest-ci.git' # For CircleCI Automatic test metadata collection
end

gem 'rest-client', '~> 2.0.1'