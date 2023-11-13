pipeline {
  agent any
  environment {
    CURRENT_BRANCH="${env.GIT_BRANCH}"
    COMMIT_HASH="${env.GIT_COMMIT}"
    KUB_PATH="k8s"
    VARS_PATH="k8s/env/prd/values-prd.yaml"
    NAMESPACE="ivanoff-bank"
    KUB_RELEASE="authn-aws-prd"
    HELM_SOURCE="https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3"
    KUB_TOKEN_NAME="authn-k8s-token"
    SERVER_URL="https://1D740396F34543A99F12858947ABAD69.gr7.eu-west-1.eks.amazonaws.com"
    HELM_FILE="helm_get_from_repo.sh"
  }
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
          def image = docker.build "cybercucumber/authn_service:${env.GIT_COMMIT}"
          docker.withRegistry('','dockerhub-authn') {
            image.push()
            image.push('latest')
          }
        }
      }
    }
    stage('Deploy HELM'){
      when {
        anyOf {
          branch "master"
        }
      }
      steps {
        withKubeConfig([credentialsId: "${KUB_TOKEN_NAME}", serverUrl: "${SERVER_URL}"]) {
        sh 'curl -fsSL -o ${HELM_FILE} ${HELM_SOURCE}'
        sh 'chmod 700 ${HELM_FILE}'
        sh './${HELM_FILE}'
        sh 'helm upgrade ${KUB_RELEASE} ${KUB_PATH} --values ${VARS_PATH} -n ${NAMESPACE} --set deployment.app.tag=${COMMIT_HASH}'
        sh 'rm ./${HELM_FILE}'
        }
      }
    }
  }
}