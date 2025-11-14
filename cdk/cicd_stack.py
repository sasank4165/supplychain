"""CI/CD Pipeline Stack for automated deployments"""
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
)
from constructs import Construct

class CICDStack(Stack):
    """CI/CD pipeline for automated testing and deployment"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # CodeCommit repository (or use GitHub/GitLab)
        repo = codecommit.Repository(
            self, "SupplyChainRepo",
            repository_name="supply-chain-agent",
            description="Supply Chain Agentic AI Application"
        )
        
        # S3 bucket for pipeline artifacts
        artifact_bucket = s3.Bucket(
            self, "PipelineArtifacts",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        # CodeBuild project for testing
        test_project = codebuild.PipelineProject(
            self, "TestProject",
            project_name="supply-chain-test",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=False
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11"
                        },
                        "commands": [
                            "pip install -r requirements.txt",
                            "pip install pytest pytest-cov"
                        ]
                    },
                    "build": {
                        "commands": [
                            "python -m pytest tests/ -v --cov=agents --cov-report=xml"
                        ]
                    }
                },
                "reports": {
                    "pytest_reports": {
                        "files": ["coverage.xml"],
                        "file-format": "COBERTURAXML"
                    }
                }
            })
        )
        
        # CodeBuild project for CDK deployment
        deploy_project = codebuild.PipelineProject(
            self, "DeployProject",
            project_name="supply-chain-deploy",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True  # Required for Docker
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11",
                            "nodejs": "18"
                        },
                        "commands": [
                            "npm install -g aws-cdk",
                            "pip install -r requirements.txt",
                            "cd cdk && pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "cd cdk",
                            "cdk synth",
                            "cdk deploy --all --require-approval never"
                        ]
                    }
                }
            })
        )
        
        # Grant permissions to deploy project
        deploy_project.add_to_role_policy(iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            resources=[f"arn:aws:iam::{self.account}:role/cdk-*"]
        ))
        
        # CodePipeline
        source_output = codepipeline.Artifact()
        test_output = codepipeline.Artifact()
        
        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name="supply-chain-pipeline",
            artifact_bucket=artifact_bucket,
            stages=[
                # Source stage
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            repository=repo,
                            branch="main",
                            output=source_output,
                            trigger=codepipeline_actions.CodeCommitTrigger.EVENTS
                        )
                    ]
                ),
                # Test stage
                codepipeline.StageProps(
                    stage_name="Test",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Unit_Tests",
                            project=test_project,
                            input=source_output,
                            outputs=[test_output]
                        )
                    ]
                ),
                # Deploy to staging
                codepipeline.StageProps(
                    stage_name="Deploy_Staging",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Deploy_to_Staging",
                            project=deploy_project,
                            input=source_output,
                            environment_variables={
                                "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value="staging")
                            }
                        )
                    ]
                ),
                # Manual approval for production
                codepipeline.StageProps(
                    stage_name="Approve_Production",
                    actions=[
                        codepipeline_actions.ManualApprovalAction(
                            action_name="Manual_Approval",
                            additional_information="Approve deployment to production"
                        )
                    ]
                ),
                # Deploy to production
                codepipeline.StageProps(
                    stage_name="Deploy_Production",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Deploy_to_Production",
                            project=deploy_project,
                            input=source_output,
                            environment_variables={
                                "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value="prod")
                            }
                        )
                    ]
                )
            ]
        )
        
        CfnOutput(self, "RepositoryCloneUrl", value=repo.repository_clone_url_http)
        CfnOutput(self, "PipelineName", value=pipeline.pipeline_name)
        CfnOutput(self, "PipelineConsoleUrl",
            value=f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline.pipeline_name}/view"
        )
