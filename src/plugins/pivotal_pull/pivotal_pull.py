#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import traceback
import requests
import pivotal_pull_settings
import plugins.plugin_base


class PivotalPull(plugins.plugin_base.PluginBase):
  activation_strings = [
      'give me a pivotal report about'
  ]
  api_endpoint = pivotal_pull_settings.API_ENDPOINT
  api_token = pivotal_pull_settings.API_TOKEN

  def _callback(self, channel, user, message):
    '''
      _callback(self, channel, user, message)
    '''
    try:
      parsed_text = self._parse_message_text(message.text)
      if parsed_text is None:
        return 'Try again. :)'
      if parsed_text['project'] == '':
        return 'What project again?'
      self.info(parsed_text)
      projects = self._get_json('projects')
      project_id = ''
      for project in projects:
        if project['name'].lower() == parsed_text['project']:
          project_id = project['id']
      if project_id == '':
        self.info('project_id was empty.')
        return 'I do not know that project.'
      state = 'state:' + ','.join(parsed_text['state'])
      owners = ''
      if parsed_text['owners'] != ['*']:
        owners = ' OR owner:'.join(parsed_text['owners'])
        owners = 'owner:' + owners
        owners = ' AND (' + owners + ')'
      types = ' OR type:'.join(parsed_text['types'])
      types = 'type:' + types
      filterr = state + owners + ' AND (' + types + ')'
      stories = self._get_json(
          'projects/' + str(project_id) + '/stories',
          {
              'filter': filterr
          }
      )
      owners = self._get_json(
          'projects/' + str(project_id) + '/memberships'
      )
      owner_id_email_map = {}
      for owner in owners:
        if parsed_text['owners'] != ['*']:
          if owner['person']['initials'].lower() not in parsed_text['owners']:
            continue
        owner_id_email_map[
            str(owner['person']['id'])
        ] = owner['person']['email']
      owner_ids = []
      owner_stories = {}
      for story in stories:
        if story['story_type'].lower() not in parsed_text['types']:
          continue
        owner_ids = story['owner_ids']
        for owner_id in owner_ids:
          owner_id = str(owner_id)
          if owner_id in owner_id_email_map:
            owner_email = owner_id_email_map[owner_id]
            owner_stories[
                owner_email
            ] = owner_stories.get(
                owner_email, []
            )
            owner_stories[owner_email].append(story)
      content = ''
      for email, stories in owner_stories.items():
        content += email + ':\n'
        counts = {
            'feature': 0,
            'chore': 0,
            'bug': 0
        }
        for i, story in enumerate(stories):
          state = story['current_state']
          typee = story['story_type']
          counts[typee] = counts.get(typee, 0) + 1
          title = story['name']
          if len(title) > 80:
            title = title[:77] + '...'
          url = story['url']
          content += '  ' + str(i) + ') ' + typee.upper() + '\t '
          content += state.upper() + '\t' + title
          content += ' ' + url
          content += '\n'
        for typee, count in counts.items():
          content += '  ' + typee.upper() + 's: ' + str(count) + ' '
        content += '\n\n'
      if content == '':
        return 'Nothing to report.'
      result = self.slack.file_upload(
          **{
              'data': {
                  'content': content,
                  'channels': channel.slack_id,
                  'title': 'Your Pivotal report.',
                  'initial_comment': '@' + user.slack_name
              }
          }
      )
      self.info(result)
      if result.get('ok', False) is True:
        if 'file' in result:
          if 'url_private' in result['file']:
            return result['file']['url_private']
    except Exception as error:
      self.error(error)
      traceback.print_exc()
      return 'Something broke...'
    return None

  def _parse_message_text(self, message_text):
    try:
      if message_text is None:
        return None
      if len(message_text) == 0:
        return None
      parsed_text = {
          'project': '',
          'state': [],
          'owners': [],
          'types': ['feature', 'bug', 'chore']
      }
      index = message_text.rfind(' about ')
      temp = message_text[index + len(' about '):].strip().split()
      parsed_text['project'] = temp[0].lower()
      parsed_text['state'] = temp[1].lower().split(',')
      parsed_text['owners'] = temp[2].lower().split(',')
      if len(temp) == 4:
        parsed_text['types'] = temp[3].lower().split(',')
      return parsed_text
    except Exception as error:
      self.error(error)
      return None
    return parsed_text

  def _get_json(self, path, params=None, headers=None):
    if params is None:
      params = {}
    if headers is None:
      headers = {}
    return requests.get(
        self.api_endpoint + path,
        params=params,
        headers=dict(
            headers.items() + {'X-TrackerToken': self.api_token}.items()
        )
    ).json()
