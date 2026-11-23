pipeline {
    agent { label 'mgmt' }

    stages {
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'gukgu-staging-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    string(credentialsId: 'gukgu-staging-host', variable: 'SSH_HOST'),
                    string(credentialsId: 'gukgu-staging-port', variable: 'SSH_PORT')
                ]) {
                    sh '''
                        echo '==> Deploying Gukgu to Staging..'
                        chmod 600 "$SSH_KEY"
                        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "$SSH_KEY" "$SSH_USER"@"$SSH_HOST" -p "$SSH_PORT" '
                            set -e
                            cd /home/projects/gukgu
                            git -C /home/projects/gukgu checkout develop
                            git -C /home/projects/gukgu pull
                            docker compose --env-file .env.staging -f docker-compose.staging.yml up -d --build --force-recreate
                            '
                        echo "Staging deployment process finished successfully!"
                    '''
                }
            }
        }
    }
}
