# TODO: this could use alot of cleanup
import os

import requests


class PelotonStack:
    get_user_stack_query = """
query ViewUserStack {
      viewUserStack {
        numClasses
        totalTime
        ... on StackResponseSuccess {
          numClasses
          totalTime
          userStack {
            stackedClassList {
              playOrder
              pelotonClass {
                joinToken
                title
                classId
                fitnessDiscipline {
                  slug
                  __typename
                }
                assets {
                  thumbnailImage {
                    location
                    __typename
                  }
                  __typename
                }
                duration
                ... on OnDemandInstructorClass {
                  joinToken
                  title
                  fitnessDiscipline {
                    slug
                    displayName
                    __typename
                  }
                  contentFormat
                  totalUserWorkouts
                  originLocale {
                    language
                    __typename
                  }
                  captions {
                    locales
                    __typename
                  }
                  timeline {
                    startOffset
                    __typename
                  }
                  difficultyLevel {
                    slug
                    displayName
                    __typename
                  }
                  airTime
                  instructor {
                    name
                    __typename
                  }
                  __typename
                }
                classTypes {
                  name
                  __typename
                }
                playableOnPlatform
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
    }
"""
    clear_user_stack_query = """
mutation ModifyStack($input: ModifyStackInput!) {
  modifyStack(input: $input) {
    numClasses
    totalTime
    userStack {
      stackedClassList {
        playOrder
        pelotonClass {
          ...ClassDetails
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment ClassDetails on PelotonClass {
  joinToken
  title
  classId
  fitnessDiscipline {
    slug
    __typename
  }
  assets {
    thumbnailImage {
      location
      __typename
    }
    __typename
  }
  duration
  ... on OnDemandInstructorClass {
    title
    fitnessDiscipline {
      slug
      displayName
      __typename
    }
    contentFormat
    difficultyLevel {
      slug
      displayName
      __typename
    }
    airTime
    instructor {
      name
      __typename
    }
    __typename
  }
  classTypes {
    name
    __typename
  }
  playableOnPlatform
  __typename
}
"""
    add_class_to_stack_query = """
mutation AddClassToStack($input: AddClassToStackInput!) {
  addClassToStack(input: $input) {
    numClasses
    totalTime
    userStack {
      stackedClassList {
        playOrder
        pelotonClass {
          ...ClassDetails
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment ClassDetails on PelotonClass {
  joinToken
  title
  classId
  fitnessDiscipline {
    slug
    __typename
  }
  assets {
    thumbnailImage {
      location
      __typename
    }
    __typename
  }
  duration
  ... on OnDemandInstructorClass {
    title
    fitnessDiscipline {
      slug
      displayName
      __typename
    }
    contentFormat
    difficultyLevel {
      slug
      displayName
      __typename
    }
    airTime
    instructor {
      name
      __typename
    }
    __typename
  }
  classTypes {
    name
    __typename
  }
  playableOnPlatform
  __typename
}
"""
    endpoint = "https://gql-graphql-gateway.prod.k8s.onepeloton.com/graphql"

    def __init__(self, peloton_session):
        self.session = peloton_session
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "peloton-scheduler",
            "Peloton-Platform": "web",
        }

    def get_stack(self):
        get_stack = {
            "operationName": "ViewUserStack",
            "variables": {},
            "query": self.get_user_stack_query,
        }
        resp = self.session.post(self.endpoint, json=get_stack, headers=self.headers)

        if not resp.ok:
            raise Exception(f"Unable to retrieve Peloton stack: {resp.status_code} - {resp._content}")

        pstack = resp.json()

        my_stack = []
        for p in pstack["data"]["viewUserStack"]["userStack"]["stackedClassList"]:
            my_stack.append(
                {
                    "Title": p["pelotonClass"]["title"],
                    "Token": p["pelotonClass"]["joinToken"],
                    "Instructor": p["pelotonClass"]["instructor"]["name"],
                    "Class Type": p["pelotonClass"]["classTypes"][0]["name"],
                    "Difficulty": p["pelotonClass"]["difficultyLevel"]["displayName"],
                }
            )
        return my_stack

    def add_class_to_stack(self, peloton_class_id):
        add_class_to_stack = {
            "operationName": "AddClassToStack",
            "variables": {"input": {"pelotonClassId": peloton_class_id}},
            "query": self.add_class_to_stack_query,
        }
        resp = self.session.post(
            self.endpoint, json=add_class_to_stack, headers=self.headers
        )

        if not resp.ok:
            raise Exception(f"Unable to add class to stack: {resp.status_code} - {resp._content}")

    def clear_stack(self):
        clear_stack = {
            "operationName": "ModifyStack",
            "variables": {"input": {"pelotonClassIdList": []}},
            "query": self.clear_user_stack_query,
        }
        resp = self.session.post(self.endpoint, json=clear_stack, headers=self.headers)

        if not resp.ok:
            raise Exception(f"Unable to clear peloton stack: {resp.status_code} - {resp._content}")


class PelotonSession:
    base_url = "https://api.onepeloton.com"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "peloton-scheduler",
    }

    def __init__(self, username, password):
        payload = {"username_or_email": username, "password": password}

        self.peloton_session = requests.Session()
        resp = self.peloton_session.post(
            f"{self.base_url}/auth/login", json=payload, headers=self.headers
        )

        if not resp.ok:
            if resp.status_code == 401:
                raise Exception(f"Invalid username or password: {resp.status_code} - {resp._content}")
            raise Exception(f"Unable to login and create a Peloton session: {resp.status_code} - {resp._content}")

        # print(resp.json()['user_id'])

    def get_bookmarked_classes(self):
        query_params = {
            "browse_category": "cycling",
            "content_format": "video",
            "limit": "18",
            "page": "0",
            "is_favorite_ride": "true",
            "sort_by": "original_air_time",
            "desc": "true",
        }

        resp = self.peloton_session.get(
            f"{self.base_url}/api/v2/ride/archived?{query_params}",
            params=query_params,
            headers=self.headers,
        )

        if not resp.ok:
            raise Exception(f"Unable to retrieve bookmarked classes: {resp.status_code} - {resp._content}")

        # print(resp._content)
        pclass = resp.json()

        instructors = {}
        for i in pclass["instructors"]:
            instructors[i["id"]] = i["name"]
        class_types = {}
        for c in pclass["class_types"]:
            class_types[c["id"]] = c["name"]

        my_classes = []
        for p in pclass["data"]:
            my_classes.append(
                {
                    "Title": p["title"],
                    "Class Type": class_types[p["ride_type_id"]],
                    "Difficulty": p["difficulty_estimate"],
                    "Token": p["join_tokens"]["on_demand"],
                    "Instructor": instructors[p["instructor_id"]],
                }
            )
            # print(p['description'])
            # print(p['fitness_discipline'])
            # print(p['ride_type_id'])
            # print(p['join_tokens'])
        return my_classes


if __name__ == "__main__":
    ps = PelotonSession(os.environ["PELOTON_USERNAME"], os.environ["PELOTON_PASSWORD"])
    stack = PelotonStack(ps.peloton_session)
    print(stack.get_stack())
    # resp = ps.add_class_to_stack("eyJob21lX3BlbG90b25faWQiOiBudWxsLCAicmlkZV9pZCI6ICIyNTA5NTgyNDYzNDI0NzQwYjgzYTUwZmVkMzAyMGRkNyIsICJzdHVkaW9fcGVsb3Rvbl9pZCI6IG51bGwsICJ0eXBlIjogIm9uX2RlbWFuZCJ9")
    # print(resp._content)
    # resp = ps.get_stack()
    # print(resp._content)
