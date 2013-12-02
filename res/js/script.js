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
    };

    $http({ method: 'GET', url: '/posts' })
        .success(function (data, status, headers, config) {
            $scope.posts = data;
    })
        .error(function (data, status, headers, config) {
    });
});