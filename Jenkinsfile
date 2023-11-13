pipeline {
  agent any
  stages {
    stage('Lint') {
      when {
        anyOf {
          branch pattern:"feature-*"
          branch pattern: "fix-*"
        }
      }
      agent {
        docker {
          image 'python:3.11.3-buster'
          args '-u 0'
        }
      }
      steps {
        sh 'pip install poetry'
        sh 'poetry install --with dev'
        sh "poetry run -- black --check *.py"
      }
    }
    stage('Build') {
      when {
        anyOf {
          branch "master"
          branch "develop"
        }
      }
      steps {
        script {
          def image = docker.build "cybercucumber/authn_service:${env.GIT_BRANCH}"
          docker.withRegistry('','dockerhub-authn') {
            image.push()
            image.push('latest')
          }
        }
      }
    }
    // stage('Deploy HELM'){
    //   when {
    //     anyOf {
    //       branch "master"
    //       branch "feature-cd-kub"
    //     }
    //     steps {
    //       sh "echo '$env'" 
    //     }
    //   }
    // }
  }
}
