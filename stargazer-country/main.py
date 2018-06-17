import os
import operator
import json
import urllib

import geotext
from graphqlclient import GraphQLClient


QUERY = '''
    query ($owner: String!, $name: String!) { 
      repository(owner: $owner, name: $name) {
        stargazers(first: 100) {
          edges {
            cursor
            node {
              login
              location
            }
          }
        }
      }
    }
    '''

QUERY_WITH_CUSOR = '''
    query ($owner: String!, $name: String!, $lastId: String) { 
      repository(owner: $owner, name: $name) {
        stargazers(first: 100, after: $lastId) {
          edges {
            cursor
            node {
              login
              location
            }
          }
        }
      }
    }
    '''

def fetch(owner, repo, lastId="", countries={}, count=0):
    client = GraphQLClient('https://api.github.com/graphql')
    # https://github.com/settings/tokens
    client.inject_token("bearer {}".format(os.environ['GITHUB_TOKEN']))

    try:
        response = client.execute(QUERY_WITH_CUSOR, {"owner": owner, "name": repo, "lastId": lastId}) if len(
            lastId) > 0 else client.execute(QUERY, {"owner": owner, "name": repo})
    except urllib.error.URLError:
        return sorted(countries.items(), key=operator.itemgetter(1), reverse=True)

    source = json.loads(response)
    if source.get('errors'):
        print(source['errors'])
        raise Exception()

    edges = source['data']['repository']['stargazers']['edges']
    if len(edges) == 0:
        return sorted(countries.items(), key=operator.itemgetter(1), reverse=True)

    cursor = edges.pop()['cursor']

    text = geotext.GeoText(response)
    for c in text.countries:
        countries[c] = countries[c] + 1 if countries.get(c) else 1

    # time.sleep(1)
    print("[{}] {}/{} {}".format(count, owner, repo, lastId))
    return fetch(owner, repo, cursor, countries, count + 1)


def main():
    slug = 'facebook/react'
    result = {}
    owner, repo = slug.split('/')
    result[repo] = fetch(owner, repo)
    for k, v in result.items():
        print("{}\t{}".format(k, k))
        for t in v:
            print("{}\t{}".format(t[0], t[1]))


if __name__ == '__main__':
    main()
