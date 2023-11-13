pipeline {
  agent any
  environment {
    CURRENT_BRANCH="${env.GIT_BRANCH}"
    REPO="https://github.com/CyberCuCuber/dos14-polikarpov_ruslan-gitflow.git"
    KUB_PATH="dos14-polikarpov_ruslan-gitflow/k8s"
    VARS_PATH="dos14-polikarpov_ruslan-gitflow/k8s/env/prd/values_prd.yaml"
    NAMESPACE="ivanoff-bank"
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
          branch "feature-cd-kub"
        }
      }
      steps {
        withKubeConfig([credentialsId: 'authn-k8s-token', serverUrl: 'https://1D740396F34543A99F12858947ABAD69.gr7.eu-west-1.eks.amazonaws.com']) {
        sh 'curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3'
        sh 'chmod 700 get_helm.sh'
        sh './get_helm.sh'
        sh 'git clone ${REPO} --branch ${CURRENT_BRANCH}'
        sh 'helm upgrade authn-aws-prd ${KUB_PATH} --values ${VARS_PATH} -n ${NAMESPACE}'
        sh 'rm ./get_helm.sh'
        sh 'rm -rf dos14-polikarpov_ruslan-gitflow'
        }
      }
    }
  }
}