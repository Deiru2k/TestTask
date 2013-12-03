/**
 * Created by ila on 01/12/13.
 */

var TestTask = angular.module('TestTask', ['ngRoute']);

TestTask.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: '/res/partials/index.html',
        controller: 'TestTaskCtrl'
      }).
      when('/groups', {
        templateUrl: '/res/partials/groups.html',
        controller: 'TestTaskGroupCtrl'
      }).
      when('/users', {
        templateUrl: '/res/partials/users.html',
        controller: 'TestTaskUserCtrl'
      })
  }]);

TestTask.controller('TestTaskCtrl', function ($scope, $http) {

    $scope.submitPost = function () {
        console.log($scope.post);
        $http({ method: 'POST', url: '/posts', data: $scope.post})
            .success(function (data, status, headers, config) {
                $scope.posts.push(data);
                $scope.apply();
            })
            .error(function (data, status, headers, config) {
                if(status == 401) {
                    alert('Unauthorized');
                }
            })
    };

    $http({ method: 'GET', url: '/posts' })
        .success(function (data, status, headers, config) {
            $scope.posts = data;
        })
        .error(function (data, status, headers, config) {
                if(status == 401) {
                    alert('Unauthorized');
                }
        })
});

TestTask.controller('TestTaskGroupCtrl', function ($scope, $http, $route) {
    $scope.update_group = function (group) {
        console.log(group);
        $http.put('/groups/' + group._id.$oid, group)
            .success(function (data, status, headers, config) {
                $route.reload();
            })
            .error(function (data, status, headers, config) {
                if(status == 401) {
                    alert('Unauthorized');
                }
            })
    }

    $scope.post_group = function() {
        $http.post('/groups', $scope.new_group)
            .success(function(data, status, headers,config) {
                $scope.groups.push(data);
                $scope.apply();
            })
            .error(function(data, status, headers, config) {
                alert('Unathorized');
            })
    }

    $http({method: 'GET', url: '/groups'})
        .success(function (data, status, headers, config) {
                $scope.groups = data;
        })
        .error(function (data, status, headers, config) {
            if(status == 401) {
                alert('Unauthorized');
            }
        })
});

TestTask.controller('TestTaskUserCtrl', function ($scope, $http, $route) {

    $scope.update_user = function(user) {
        $http.put('/users/' + user._id.$oid, user)
            .success(function (data, status, headers, config) {
                $route.reload();
            })
            .error(function (data, status, headers, config) {
                if(status == 401) {
                    alert('Unauthorized');
                }
            })
    }

    $http.get('/users')
        .success(function (data, status, headers, config) {
                $scope.users = data;
        })
        .error(function (data, status, headers, config) {
            if(status == 401) {
                alert('Unauthorized');
            }
        })
})