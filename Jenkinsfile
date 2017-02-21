node('master'){
    switch(env.BRANCH_NAME) {
        case "master":
            environment = "staging"
        break
        case "production":
            environment = "production"
        break
        default:
            print "Invalid branch"
            currentBuild.result = "FAILURE"
            throw err
        break
    }
    type = 'group'
}

node('mesos') {
    def image
    def params
    def app_id = "remo"
    def dockerRegistry = "docker-registry.ops.mozilla.community:443"

    stage('Prep') {
        checkout scm
        gitCommit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
        params = [string(name: 'environment', value: environment),
                  string(name: 'commit_id', value: gitCommit),
                  string(name: 'marathon_id', value: app_id),
                  string(name: 'marathon_config', value: 'remo_' + environment + '.json'),
                  string(name: 'type', value: 'group')]
    }

    stage('Build') {
        image = docker.build(app_id + ":" + gitCommit, "-f docker/prod .")
    }

    stage('Push') {
        sh "docker tag ${image.imageName()} " + dockerRegistry + "/${image.imageName()}"
        sh "docker push " + dockerRegistry + "/${image.imageName()}"
    }

    stage('Deploy') {
        build job: 'deploy-test', parameters: params
    }
}
