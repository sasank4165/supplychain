"""WAF Stack for API Gateway protection"""
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_wafv2 as waf,
)
from constructs import Construct

class WAFStack(Stack):
    """Web Application Firewall for API protection"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # WAF Web ACL
        self.web_acl = waf.CfnWebACL(
            self, "SupplyChainWebACL",
            scope="REGIONAL",
            default_action=waf.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="SupplyChainWebACL",
                sampled_requests_enabled=True
            ),
            name="supply-chain-web-acl",
            rules=[
                # AWS Managed Rules - Core Rule Set
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    override_action=waf.CfnWebACL.OverrideActionProperty(none={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSetMetric",
                        sampled_requests_enabled=True
                    )
                ),
                # AWS Managed Rules - Known Bad Inputs
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesKnownBadInputsRuleSet",
                    priority=2,
                    override_action=waf.CfnWebACL.OverrideActionProperty(none={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesKnownBadInputsRuleSet"
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesKnownBadInputsRuleSetMetric",
                        sampled_requests_enabled=True
                    )
                ),
                # Rate limiting rule - 2000 requests per 5 minutes per IP
                waf.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=3,
                    action=waf.CfnWebACL.RuleActionProperty(
                        block=waf.CfnWebACL.BlockActionProperty(
                            custom_response=waf.CfnWebACL.CustomResponseProperty(
                                response_code=429
                            )
                        )
                    ),
                    statement=waf.CfnWebACL.StatementProperty(
                        rate_based_statement=waf.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,
                            aggregate_key_type="IP"
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule",
                        sampled_requests_enabled=True
                    )
                ),
                # Geo blocking rule (optional - block specific countries)
                waf.CfnWebACL.RuleProperty(
                    name="GeoBlockRule",
                    priority=4,
                    action=waf.CfnWebACL.RuleActionProperty(block={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        not_statement=waf.CfnWebACL.NotStatementProperty(
                            statement=waf.CfnWebACL.StatementProperty(
                                geo_match_statement=waf.CfnWebACL.GeoMatchStatementProperty(
                                    country_codes=["US", "CA", "GB", "DE", "FR", "IN", "AU"]  # Allowed countries
                                )
                            )
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="GeoBlockRule",
                        sampled_requests_enabled=True
                    )
                ),
                # SQL Injection protection
                waf.CfnWebACL.RuleProperty(
                    name="SQLInjectionRule",
                    priority=5,
                    action=waf.CfnWebACL.RuleActionProperty(block={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        or_statement=waf.CfnWebACL.OrStatementProperty(
                            statements=[
                                waf.CfnWebACL.StatementProperty(
                                    sqli_match_statement=waf.CfnWebACL.SqliMatchStatementProperty(
                                        field_to_match=waf.CfnWebACL.FieldToMatchProperty(
                                            body=waf.CfnWebACL.BodyProperty(
                                                oversize_handling="CONTINUE"
                                            )
                                        ),
                                        text_transformations=[
                                            waf.CfnWebACL.TextTransformationProperty(
                                                priority=0,
                                                type="URL_DECODE"
                                            )
                                        ]
                                    )
                                ),
                                waf.CfnWebACL.StatementProperty(
                                    sqli_match_statement=waf.CfnWebACL.SqliMatchStatementProperty(
                                        field_to_match=waf.CfnWebACL.FieldToMatchProperty(
                                            query_string={}
                                        ),
                                        text_transformations=[
                                            waf.CfnWebACL.TextTransformationProperty(
                                                priority=0,
                                                type="URL_DECODE"
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="SQLInjectionRule",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )
        
        CfnOutput(self, "WebACLArn", value=self.web_acl.attr_arn)
        CfnOutput(self, "WebACLId", value=self.web_acl.attr_id)
