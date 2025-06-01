"""
OpenDistillery Salesforce Integration
Enterprise-grade Salesforce CRM integration with compound AI capabilities
for intelligent sales automation, lead scoring, and customer insights.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

# Salesforce integration
try:
    from simple_salesforce import Salesforce, SalesforceLogin
    import requests
except ImportError:
    logger.warning("Salesforce SDK not installed - some features may be limited")

from ..agents.base_agent import BaseAgent, AgentCapability
from ..agents.orchestrator import AgentOrchestrator, Task, TaskPriority

import structlog

logger = structlog.get_logger(__name__)

@dataclass
class SalesforceConfig:
    """Salesforce connection configuration"""
    username: str
    password: str
    security_token: str
    domain: str = "login"  # or "test" for sandbox
    api_version: str = "58.0"
    oauth_settings: Optional[Dict[str, str]] = None

class SalesforceAIIntegration:
    """
    Enterprise Salesforce integration with compound AI capabilities
    """
    
    def __init__(self, config: SalesforceConfig, orchestrator: AgentOrchestrator):
        self.config = config
        self.orchestrator = orchestrator
        self.sf_client: Optional[Salesforce] = None
        
        # Specialized AI agents for Salesforce
        self.lead_scoring_agent = None
        self.opportunity_analyzer = None
        self.customer_insights_agent = None
        self.email_assistant = None
        
        # Integration metrics
        self.integration_metrics = {
            "api_calls_made": 0,
            "ai_predictions": 0,
            "leads_analyzed": 0,
            "opportunities_analyzed": 0,
            "emails_generated": 0,
            "success_rate": 1.0
        }
        
        self._initialize_ai_agents()
    
    async def initialize(self) -> bool:
        """Initialize Salesforce connection and AI capabilities"""
        try:
            # Connect to Salesforce
            self.sf_client = Salesforce(
                username=self.config.username,
                password=self.config.password,
                security_token=self.config.security_token,
                domain=self.config.domain,
                version=self.config.api_version
            )
            
            # Test connection
            user_info = self.sf_client.query("SELECT Id, Name FROM User LIMIT 1")
            logger.info(f"Connected to Salesforce as: {user_info['records'][0]['Name']}")
            
            # Register AI agents with orchestrator
            await self._register_ai_agents()
            
            logger.info("Salesforce AI integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce integration: {str(e)}")
            return False
    
    def _initialize_ai_agents(self) -> None:
        """Initialize specialized AI agents for Salesforce operations"""
        # Lead Scoring Agent
        self.lead_scoring_agent = BaseAgent(
            agent_id="salesforce_lead_scorer",
            agent_type="financial_analyst",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.PREDICTION, AgentCapability.CLASSIFICATION]
        )
        
        # Opportunity Analysis Agent
        self.opportunity_analyzer = BaseAgent(
            agent_id="salesforce_opportunity_analyzer",
            agent_type="business_analyst",
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.REASONING, AgentCapability.PREDICTION]
        )
        
        # Customer Insights Agent
        self.customer_insights_agent = BaseAgent(
            agent_id="salesforce_customer_insights",
            agent_type="research_scientist",
            capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS, AgentCapability.SYNTHESIS]
        )
        
        # Email Assistant Agent
        self.email_assistant = BaseAgent(
            agent_id="salesforce_email_assistant",
            agent_type="content_creator",
            capabilities=[AgentCapability.CONTENT_GENERATION, AgentCapability.COMMUNICATION]
        )
        
        # Register specialized tools
        self._register_specialized_tools()
    
    def _register_specialized_tools(self) -> None:
        """Register Salesforce-specific tools for agents"""
        # Lead scoring tools
        self.lead_scoring_agent.register_tool(
            "calculate_lead_score",
            self._calculate_lead_score,
            "Calculate AI-powered lead score based on multiple factors"
        )
        
        self.lead_scoring_agent.register_tool(
            "analyze_lead_behavior",
            self._analyze_lead_behavior,
            "Analyze lead behavior patterns and engagement"
        )
        
        # Opportunity analysis tools
        self.opportunity_analyzer.register_tool(
            "predict_win_probability",
            self._predict_win_probability,
            "Predict opportunity win probability using AI models"
        )
        
        self.opportunity_analyzer.register_tool(
            "identify_risk_factors",
            self._identify_risk_factors,
            "Identify potential risk factors for opportunities"
        )
        
        # Customer insights tools
        self.customer_insights_agent.register_tool(
            "analyze_customer_health",
            self._analyze_customer_health,
            "Analyze customer health score and churn risk"
        )
        
        self.customer_insights_agent.register_tool(
            "identify_upsell_opportunities",
            self._identify_upsell_opportunities,
            "Identify potential upsell and cross-sell opportunities"
        )
        
        # Email generation tools
        self.email_assistant.register_tool(
            "generate_personalized_email",
            self._generate_personalized_email,
            "Generate personalized email content for prospects"
        )
    
    async def _register_ai_agents(self) -> None:
        """Register AI agents with the orchestrator"""
        agents = [
            self.lead_scoring_agent,
            self.opportunity_analyzer,
            self.customer_insights_agent,
            self.email_assistant
        ]
        
        for agent in agents:
            if agent:
                self.orchestrator.register_agent(agent)
        
        logger.info("Salesforce AI agents registered with orchestrator")
    
    # Lead Management with AI
    
    async def analyze_lead(self, lead_id: str) -> Dict[str, Any]:
        """Comprehensive AI analysis of a Salesforce lead"""
        try:
            start_time = time.time()
            
            # Get lead data from Salesforce
            lead_data = await self._get_lead_data(lead_id)
            if not lead_data:
                return {"error": "Lead not found"}
            
            # Create AI analysis task
            analysis_task = Task(
                task_id=f"lead_analysis_{lead_id}",
                task_type="lead_analysis",
                description=f"Comprehensive analysis of lead {lead_id}",
                input_data={
                    "lead_data": lead_data,
                    "analysis_types": [
                        "lead_quality_score",
                        "conversion_probability",
                        "behavioral_analysis",
                        "recommended_actions"
                    ]
                },
                required_capabilities=[AgentCapability.ANALYSIS, AgentCapability.PREDICTION],
                priority=TaskPriority.HIGH,
                context={"integration": "salesforce", "object_type": "lead"}
            )
            
            # Submit task to orchestrator
            task_id = await self.orchestrator.submit_task(analysis_task)
            
            # Wait for completion (with timeout)
            result = await self._wait_for_task_completion(task_id, timeout=30)
            
            if result and result.success:
                ai_insights = result.result_data
                
                # Update lead in Salesforce with AI insights
                await self._update_lead_with_ai_insights(lead_id, ai_insights)
                
                processing_time = time.time() - start_time
                self._update_metrics("ai_predictions", "leads_analyzed")
                
                return {
                    "lead_id": lead_id,
                    "ai_analysis": ai_insights,
                    "processing_time": processing_time,
                    "success": True
                }
            else:
                return {"error": "AI analysis failed", "details": result.error_message if result else "Unknown error"}
                
        except Exception as e:
            logger.error(f"Error analyzing lead {lead_id}: {str(e)}")
            return {"error": str(e)}
    
    async def batch_analyze_leads(self, lead_filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Batch analyze multiple leads with AI"""
        try:
            # Get leads from Salesforce
            leads = await self._get_leads(lead_filters)
            
            if not leads:
                return {"message": "No leads found", "analyzed_count": 0}
            
            # Create batch analysis tasks
            analysis_tasks = []
            for lead in leads[:50]:  # Limit batch size
                task = Task(
                    task_id=f"batch_lead_analysis_{lead['Id']}",
                    task_type="lead_analysis",
                    description=f"Batch analysis of lead {lead['Id']}",
                    input_data={"lead_data": lead},
                    required_capabilities=[AgentCapability.ANALYSIS],
                    priority=TaskPriority.MEDIUM
                )
                analysis_tasks.append(task)
            
            # Submit all tasks
            task_ids = []
            for task in analysis_tasks:
                task_id = await self.orchestrator.submit_task(task)
                task_ids.append(task_id)
            
            # Wait for all completions
            results = await self._wait_for_multiple_tasks(task_ids, timeout=60)
            
            # Process results
            successful_analyses = [r for r in results if r and r.success]
            failed_analyses = [r for r in results if r and not r.success]
            
            # Generate batch insights
            batch_insights = self._generate_batch_insights(successful_analyses)
            
            self._update_metrics("ai_predictions", count=len(successful_analyses))
            self._update_metrics("leads_analyzed", count=len(successful_analyses))
            
            return {
                "total_leads": len(leads),
                "analyzed_successfully": len(successful_analyses),
                "failed_analyses": len(failed_analyses),
                "batch_insights": batch_insights,
                "individual_results": [r.result_data for r in successful_analyses]
            }
            
        except Exception as e:
            logger.error(f"Error in batch lead analysis: {str(e)}")
            return {"error": str(e)}
    
    # Opportunity Management
    
    async def analyze_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        """AI-powered opportunity analysis"""
        try:
            # Get opportunity data
            opp_data = await self._get_opportunity_data(opportunity_id)
            if not opp_data:
                return {"error": "Opportunity not found"}
            
            # Create analysis task
            analysis_task = Task(
                task_id=f"opportunity_analysis_{opportunity_id}",
                task_type="opportunity_analysis",
                description=f"AI analysis of opportunity {opportunity_id}",
                input_data={
                    "opportunity_data": opp_data,
                    "analysis_goals": [
                        "win_probability",
                        "deal_value_prediction",
                        "timeline_forecast",
                        "risk_assessment",
                        "next_best_actions"
                    ]
                },
                required_capabilities=[AgentCapability.ANALYSIS, AgentCapability.PREDICTION],
                priority=TaskPriority.HIGH,
                context={"integration": "salesforce", "object_type": "opportunity"}
            )
            
            # Submit and wait for analysis
            task_id = await self.orchestrator.submit_task(analysis_task)
            result = await self._wait_for_task_completion(task_id, timeout=30)
            
            if result and result.success:
                ai_insights = result.result_data
                
                # Update opportunity with AI insights
                await self._update_opportunity_with_ai_insights(opportunity_id, ai_insights)
                
                self._update_metrics("ai_predictions", "opportunities_analyzed")
                
                return {
                    "opportunity_id": opportunity_id,
                    "ai_analysis": ai_insights,
                    "success": True
                }
            else:
                return {"error": "AI analysis failed"}
                
        except Exception as e:
            logger.error(f"Error analyzing opportunity {opportunity_id}: {str(e)}")
            return {"error": str(e)}
    
    # Customer Insights
    
    async def generate_customer_insights(self, account_id: str) -> Dict[str, Any]:
        """Generate comprehensive customer insights using AI"""
        try:
            # Get customer data
            customer_data = await self._get_customer_data(account_id)
            
            # Create insights task
            insights_task = Task(
                task_id=f"customer_insights_{account_id}",
                task_type="customer_insights",
                description=f"Generate insights for customer {account_id}",
                input_data={
                    "customer_data": customer_data,
                    "insight_types": [
                        "health_score",
                        "churn_risk",
                        "upsell_potential",
                        "engagement_patterns",
                        "satisfaction_indicators"
                    ]
                },
                required_capabilities=[AgentCapability.ANALYSIS, AgentCapability.RESEARCH],
                priority=TaskPriority.MEDIUM
            )
            
            task_id = await self.orchestrator.submit_task(insights_task)
            result = await self._wait_for_task_completion(task_id, timeout=45)
            
            if result and result.success:
                insights = result.result_data
                
                # Update customer record
                await self._update_account_with_insights(account_id, insights)
                
                return {
                    "account_id": account_id,
                    "customer_insights": insights,
                    "success": True
                }
            else:
                return {"error": "Insights generation failed"}
                
        except Exception as e:
            logger.error(f"Error generating customer insights for {account_id}: {str(e)}")
            return {"error": str(e)}
    
    # Email AI Assistant
    
    async def generate_email_content(self, 
                                   email_type: str,
                                   recipient_data: Dict[str, Any],
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate personalized email content using AI"""
        try:
            # Create email generation task
            email_task = Task(
                task_id=f"email_generation_{int(time.time())}",
                task_type="email_generation",
                description=f"Generate {email_type} email",
                input_data={
                    "email_type": email_type,
                    "recipient_data": recipient_data,
                    "context": context or {},
                    "requirements": [
                        "personalized_subject",
                        "engaging_content",
                        "clear_call_to_action",
                        "professional_tone"
                    ]
                },
                required_capabilities=[AgentCapability.CONTENT_GENERATION, AgentCapability.COMMUNICATION],
                priority=TaskPriority.MEDIUM
            )
            
            task_id = await self.orchestrator.submit_task(email_task)
            result = await self._wait_for_task_completion(task_id, timeout=20)
            
            if result and result.success:
                email_content = result.result_data
                
                self._update_metrics("emails_generated")
                
                return {
                    "success": True,
                    "email_content": email_content,
                    "generation_metadata": {
                        "email_type": email_type,
                        "processing_time": result.execution_time
                    }
                }
            else:
                return {"error": "Email generation failed"}
                
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            return {"error": str(e)}
    
    # Salesforce Data Access Methods
    
    async def _get_lead_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive lead data from Salesforce"""
        try:
            query = f"""
            SELECT Id, FirstName, LastName, Company, Email, Phone, Status,
                   Source, Industry, AnnualRevenue, NumberOfEmployees,
                   CreatedDate, LastModifiedDate, ConvertedDate,
                   AI_Lead_Score__c, AI_Conversion_Probability__c
            FROM Lead 
            WHERE Id = '{lead_id}'
            """
            
            result = self.sf_client.query(query)
            self._update_metrics("api_calls_made")
            
            if result["records"]:
                lead_data = result["records"][0]
                
                # Enrich with activity data
                activities = await self._get_lead_activities(lead_id)
                lead_data["activities"] = activities
                
                return lead_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting lead data for {lead_id}: {str(e)}")
            return None
    
    async def _get_leads(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get leads with optional filters"""
        try:
            base_query = """
            SELECT Id, FirstName, LastName, Company, Email, Status,
                   CreatedDate, AI_Lead_Score__c
            FROM Lead
            """
            
            where_conditions = []
            if filters:
                if filters.get("status"):
                    where_conditions.append(f"Status = '{filters['status']}'")
                if filters.get("created_after"):
                    where_conditions.append(f"CreatedDate >= {filters['created_after']}")
                if filters.get("min_score"):
                    where_conditions.append(f"AI_Lead_Score__c >= {filters['min_score']}")
            
            if where_conditions:
                query = base_query + " WHERE " + " AND ".join(where_conditions)
            else:
                query = base_query + " LIMIT 100"
            
            result = self.sf_client.query(query)
            self._update_metrics("api_calls_made")
            
            return result["records"]
            
        except Exception as e:
            logger.error(f"Error getting leads: {str(e)}")
            return []
    
    async def _get_opportunity_data(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive opportunity data"""
        try:
            query = f"""
            SELECT Id, Name, AccountId, Amount, CloseDate, StageName, Probability,
                   Type, LeadSource, CreatedDate, LastModifiedDate,
                   AI_Win_Probability__c, AI_Predicted_Value__c
            FROM Opportunity 
            WHERE Id = '{opportunity_id}'
            """
            
            result = self.sf_client.query(query)
            self._update_metrics("api_calls_made")
            
            if result["records"]:
                opp_data = result["records"][0]
                
                # Enrich with related data
                activities = await self._get_opportunity_activities(opportunity_id)
                opp_data["activities"] = activities
                
                return opp_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting opportunity data: {str(e)}")
            return None
    
    async def _get_customer_data(self, account_id: str) -> Dict[str, Any]:
        """Get comprehensive customer data"""
        try:
            # Get account data
            account_query = f"""
            SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees,
                   Type, CreatedDate, LastModifiedDate
            FROM Account 
            WHERE Id = '{account_id}'
            """
            
            account_result = self.sf_client.query(account_query)
            
            if not account_result["records"]:
                return {}
            
            customer_data = account_result["records"][0]
            
            # Get related opportunities
            opp_query = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, CreatedDate
            FROM Opportunity 
            WHERE AccountId = '{account_id}'
            ORDER BY CreatedDate DESC
            LIMIT 10
            """
            
            opp_result = self.sf_client.query(opp_query)
            customer_data["opportunities"] = opp_result["records"]
            
            # Get support cases
            case_query = f"""
            SELECT Id, Subject, Status, Priority, CreatedDate, ClosedDate
            FROM Case 
            WHERE AccountId = '{account_id}'
            ORDER BY CreatedDate DESC
            LIMIT 20
            """
            
            case_result = self.sf_client.query(case_query)
            customer_data["support_cases"] = case_result["records"]
            
            self._update_metrics("api_calls_made", count=3)
            return customer_data
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return {}
    
    async def _get_lead_activities(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get lead activities and engagement data"""
        try:
            query = f"""
            SELECT Id, Subject, ActivityDate, Type, Status, Description
            FROM Task
            WHERE WhoId = '{lead_id}'
            ORDER BY ActivityDate DESC
            LIMIT 20
            """
            
            result = self.sf_client.query(query)
            return result["records"]
            
        except Exception as e:
            logger.error(f"Error getting lead activities: {str(e)}")
            return []
    
    async def _get_opportunity_activities(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """Get opportunity activities"""
        try:
            query = f"""
            SELECT Id, Subject, ActivityDate, Type, Status, Description
            FROM Task
            WHERE WhatId = '{opportunity_id}'
            ORDER BY ActivityDate DESC
            LIMIT 20
            """
            
            result = self.sf_client.query(query)
            return result["records"]
            
        except Exception as e:
            logger.error(f"Error getting opportunity activities: {str(e)}")
            return []
    
    # AI Tool Implementations
    
    async def _calculate_lead_score(self, **kwargs) -> Dict[str, Any]:
        """Calculate AI-powered lead score"""
        lead_data = kwargs.get("lead_data", {})
        
        # Implement sophisticated lead scoring algorithm
        score = 0.0
        factors = []
        
        # Company size factor
        employees = lead_data.get("NumberOfEmployees", 0)
        if employees > 1000:
            score += 0.3
            factors.append("Large company (1000+ employees)")
        elif employees > 100:
            score += 0.2
            factors.append("Medium company (100+ employees)")
        
        # Revenue factor
        revenue = lead_data.get("AnnualRevenue", 0)
        if revenue > 10000000:  # $10M+
            score += 0.25
            factors.append("High revenue company")
        elif revenue > 1000000:  # $1M+
            score += 0.15
            factors.append("Medium revenue company")
        
        # Industry factor
        industry = lead_data.get("Industry", "")
        high_value_industries = ["Technology", "Financial Services", "Healthcare"]
        if industry in high_value_industries:
            score += 0.2
            factors.append(f"High-value industry: {industry}")
        
        # Engagement factor
        activities = lead_data.get("activities", [])
        if len(activities) > 5:
            score += 0.15
            factors.append("High engagement (5+ activities)")
        elif len(activities) > 2:
            score += 0.1
            factors.append("Medium engagement")
        
        # Source factor
        source = lead_data.get("Source", "")
        high_quality_sources = ["Referral", "Partner", "Website"]
        if source in high_quality_sources:
            score += 0.1
            factors.append(f"Quality source: {source}")
        
        # Normalize score to 0-1 range
        score = min(score, 1.0)
        
        return {
            "lead_score": score,
            "score_grade": self._score_to_grade(score),
            "contributing_factors": factors,
            "confidence": 0.85
        }
    
    async def _analyze_lead_behavior(self, **kwargs) -> Dict[str, Any]:
        """Analyze lead behavior patterns"""
        lead_data = kwargs.get("lead_data", {})
        activities = lead_data.get("activities", [])
        
        behavior_analysis = {
            "engagement_level": "low",
            "response_pattern": "irregular",
            "interest_indicators": [],
            "risk_factors": []
        }
        
        if len(activities) > 10:
            behavior_analysis["engagement_level"] = "high"
            behavior_analysis["interest_indicators"].append("Frequent interactions")
        elif len(activities) > 5:
            behavior_analysis["engagement_level"] = "medium"
        
        # Analyze activity types
        activity_types = [a.get("Type", "") for a in activities]
        if "Email" in activity_types:
            behavior_analysis["interest_indicators"].append("Email engagement")
        if "Call" in activity_types:
            behavior_analysis["interest_indicators"].append("Phone engagement")
        
        return behavior_analysis
    
    async def _predict_win_probability(self, **kwargs) -> Dict[str, Any]:
        """Predict opportunity win probability"""
        opp_data = kwargs.get("opportunity_data", {})
        
        # Implement win probability prediction
        base_probability = 0.3  # Base 30%
        
        # Stage factor
        stage = opp_data.get("StageName", "")
        stage_probabilities = {
            "Prospecting": 0.1,
            "Qualification": 0.2,
            "Needs Analysis": 0.3,
            "Value Proposition": 0.4,
            "Proposal": 0.6,
            "Negotiation": 0.8,
            "Closed Won": 1.0,
            "Closed Lost": 0.0
        }
        
        probability = stage_probabilities.get(stage, base_probability)
        
        # Adjust based on amount
        amount = opp_data.get("Amount", 0)
        if amount > 100000:  # Large deals
            probability *= 0.9  # Slightly lower probability
        elif amount < 10000:  # Small deals
            probability *= 1.1  # Slightly higher probability
        
        # Activity factor
        activities = opp_data.get("activities", [])
        if len(activities) > 10:
            probability *= 1.1
        elif len(activities) < 3:
            probability *= 0.9
        
        probability = min(probability, 1.0)
        
        return {
            "win_probability": probability,
            "confidence": 0.8,
            "key_factors": [
                f"Current stage: {stage}",
                f"Deal size: ${amount:,.0f}",
                f"Activity level: {len(activities)} interactions"
            ]
        }
    
    async def _identify_risk_factors(self, **kwargs) -> Dict[str, Any]:
        """Identify opportunity risk factors"""
        opp_data = kwargs.get("opportunity_data", {})
        
        risk_factors = []
        risk_score = 0.0
        
        # Timeline risk
        close_date = opp_data.get("CloseDate")
        if close_date:
            # Parse date and check if it's soon
            try:
                from datetime import datetime
                close_dt = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
                days_to_close = (close_dt - datetime.now()).days
                
                if days_to_close < 7:
                    risk_factors.append("Very tight timeline (< 1 week)")
                    risk_score += 0.3
                elif days_to_close < 30:
                    risk_factors.append("Tight timeline (< 1 month)")
                    risk_score += 0.15
            except:
                pass
        
        # Low activity risk
        activities = opp_data.get("activities", [])
        if len(activities) < 3:
            risk_factors.append("Low engagement activity")
            risk_score += 0.2
        
        # Large deal risk
        amount = opp_data.get("Amount", 0)
        if amount > 500000:
            risk_factors.append("Large deal size increases complexity")
            risk_score += 0.1
        
        # Stage stagnation risk (would need historical data)
        risk_factors.append("Monitor for stage progression")
        
        return {
            "risk_factors": risk_factors,
            "overall_risk_score": min(risk_score, 1.0),
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.2 else "low"
        }
    
    async def _analyze_customer_health(self, **kwargs) -> Dict[str, Any]:
        """Analyze customer health score"""
        customer_data = kwargs.get("customer_data", {})
        
        health_score = 0.8  # Start with good health
        health_factors = []
        
        # Support case analysis
        support_cases = customer_data.get("support_cases", [])
        open_cases = [c for c in support_cases if c.get("Status") != "Closed"]
        
        if len(open_cases) > 5:
            health_score -= 0.3
            health_factors.append("High number of open support cases")
        elif len(open_cases) > 2:
            health_score -= 0.1
            health_factors.append("Some open support cases")
        
        # Opportunity activity
        opportunities = customer_data.get("opportunities", [])
        recent_opps = [o for o in opportunities if o.get("CreatedDate", "") > "2023-01-01"]
        
        if len(recent_opps) > 2:
            health_score += 0.1
            health_factors.append("Active opportunity pipeline")
        elif len(recent_opps) == 0:
            health_score -= 0.2
            health_factors.append("No recent opportunities")
        
        health_score = max(0.0, min(1.0, health_score))
        
        return {
            "health_score": health_score,
            "health_grade": self._score_to_grade(health_score),
            "contributing_factors": health_factors,
            "churn_risk": 1.0 - health_score
        }
    
    async def _identify_upsell_opportunities(self, **kwargs) -> Dict[str, Any]:
        """Identify upsell and cross-sell opportunities"""
        customer_data = kwargs.get("customer_data", {})
        
        upsell_score = 0.5
        opportunities = []
        
        # Analyze current opportunities
        current_opps = customer_data.get("opportunities", [])
        won_opps = [o for o in current_opps if o.get("StageName") == "Closed Won"]
        
        if len(won_opps) > 2:
            upsell_score += 0.2
            opportunities.append("Multiple successful deals indicate expansion potential")
        
        # Company size factor
        employees = customer_data.get("NumberOfEmployees", 0)
        if employees > 500:
            upsell_score += 0.2
            opportunities.append("Large organization with expansion potential")
        
        # Revenue factor
        revenue = customer_data.get("AnnualRevenue", 0)
        if revenue > 50000000:  # $50M+
            upsell_score += 0.15
            opportunities.append("High-revenue company suitable for premium offerings")
        
        return {
            "upsell_score": min(upsell_score, 1.0),
            "upsell_opportunities": opportunities,
            "recommended_approach": "Strategic account expansion" if upsell_score > 0.7 else "Standard upsell process"
        }
    
    async def _generate_personalized_email(self, **kwargs) -> Dict[str, Any]:
        """Generate personalized email content"""
        email_type = kwargs.get("email_type", "follow_up")
        recipient_data = kwargs.get("recipient_data", {})
        context = kwargs.get("context", {})
        
        # Email templates based on type
        email_templates = {
            "follow_up": {
                "subject": "Following up on our conversation about {company}",
                "opening": "Hi {first_name},\n\nI wanted to follow up on our recent conversation about {company}'s needs.",
                "body": "Based on our discussion, I believe our solution could help {company} achieve {benefit}. I'd love to schedule a brief call to explore this further.",
                "closing": "Looking forward to hearing from you.\n\nBest regards"
            },
            "proposal": {
                "subject": "Proposal for {company} - {solution}",
                "opening": "Hi {first_name},\n\nThank you for your time yesterday. As promised, I'm attaching our proposal for {company}.",
                "body": "Our solution addresses the key challenges we discussed: {challenges}. The proposal includes pricing, timeline, and implementation details.",
                "closing": "I'm available to discuss any questions you might have.\n\nBest regards"
            }
        }
        
        template = email_templates.get(email_type, email_templates["follow_up"])
        
        # Personalize with recipient data
        first_name = recipient_data.get("FirstName", "there")
        company = recipient_data.get("Company", "your organization")
        
        # Generate personalized content
        subject = template["subject"].format(company=company, first_name=first_name)
        content = f"{template['opening']}\n\n{template['body']}\n\n{template['closing']}"
        
        # Apply personalization
        content = content.format(
            first_name=first_name,
            company=company,
            benefit="improve efficiency and reduce costs",  # Would be context-specific
            solution="our AI platform",
            challenges="operational efficiency and data management"
        )
        
        return {
            "subject": subject,
            "body": content,
            "tone": "professional",
            "personalization_score": 0.8,
            "call_to_action": "Schedule a follow-up call"
        }
    
    # Update Methods
    
    async def _update_lead_with_ai_insights(self, lead_id: str, insights: Dict[str, Any]) -> bool:
        """Update lead record with AI insights"""
        try:
            update_data = {
                "AI_Lead_Score__c": insights.get("lead_score", 0) * 100,
                "AI_Last_Analyzed__c": datetime.now().isoformat(),
                "AI_Score_Grade__c": insights.get("score_grade", "C")
            }
            
            self.sf_client.Lead.update(lead_id, update_data)
            self._update_metrics("api_calls_made")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lead {lead_id}: {str(e)}")
            return False
    
    async def _update_opportunity_with_ai_insights(self, opp_id: str, insights: Dict[str, Any]) -> bool:
        """Update opportunity record with AI insights"""
        try:
            update_data = {
                "AI_Win_Probability__c": insights.get("win_probability", 0) * 100,
                "AI_Last_Analyzed__c": datetime.now().isoformat(),
                "AI_Risk_Level__c": insights.get("risk_level", "medium")
            }
            
            self.sf_client.Opportunity.update(opp_id, update_data)
            self._update_metrics("api_calls_made")
            return True
            
        except Exception as e:
            logger.error(f"Error updating opportunity {opp_id}: {str(e)}")
            return False
    
    async def _update_account_with_insights(self, account_id: str, insights: Dict[str, Any]) -> bool:
        """Update account record with customer insights"""
        try:
            update_data = {
                "AI_Health_Score__c": insights.get("health_score", 0.5) * 100,
                "AI_Churn_Risk__c": insights.get("churn_risk", 0.5) * 100,
                "AI_Upsell_Score__c": insights.get("upsell_score", 0.5) * 100,
                "AI_Last_Analyzed__c": datetime.now().isoformat()
            }
            
            self.sf_client.Account.update(account_id, update_data)
            self._update_metrics("api_calls_made")
            return True
            
        except Exception as e:
            logger.error(f"Error updating account {account_id}: {str(e)}")
            return False
    
    # Utility Methods
    
    async def _wait_for_task_completion(self, task_id: str, timeout: int = 30) -> Optional[Any]:
        """Wait for task completion with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.orchestrator.completed_tasks:
                return self.orchestrator.completed_tasks[task_id]
            
            await asyncio.sleep(0.5)
        
        logger.warning(f"Task {task_id} timed out after {timeout} seconds")
        return None
    
    async def _wait_for_multiple_tasks(self, task_ids: List[str], timeout: int = 60) -> List[Any]:
        """Wait for multiple tasks to complete"""
        results = []
        start_time = time.time()
        
        completed_tasks = set()
        
        while len(completed_tasks) < len(task_ids) and time.time() - start_time < timeout:
            for task_id in task_ids:
                if task_id not in completed_tasks and task_id in self.orchestrator.completed_tasks:
                    results.append(self.orchestrator.completed_tasks[task_id])
                    completed_tasks.add(task_id)
            
            await asyncio.sleep(0.5)
        
        # Add None for incomplete tasks
        while len(results) < len(task_ids):
            results.append(None)
        
        return results
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        else:
            return "D"
    
    def _generate_batch_insights(self, results: List[Any]) -> Dict[str, Any]:
        """Generate insights from batch analysis results"""
        if not results:
            return {}
        
        # Extract scores from results
        scores = []
        for result in results:
            if result and result.result_data:
                score = result.result_data.get("lead_score", 0)
                scores.append(score)
        
        if not scores:
            return {}
        
        import numpy as np
        
        return {
            "total_analyzed": len(results),
            "average_score": np.mean(scores),
            "high_quality_leads": len([s for s in scores if s > 0.8]),
            "score_distribution": {
                "A_grade": len([s for s in scores if s >= 0.8]),
                "B_grade": len([s for s in scores if 0.6 <= s < 0.8]),
                "C_grade": len([s for s in scores if 0.4 <= s < 0.6]),
                "D_grade": len([s for s in scores if s < 0.4])
            },
            "recommendations": [
                "Focus on A-grade leads for immediate follow-up",
                "Develop nurture campaigns for B and C grade leads",
                "Review D-grade leads for disqualification"
            ]
        }
    
    def _update_metrics(self, *metric_names, count: int = 1) -> None:
        """Update integration metrics"""
        for metric_name in metric_names:
            if metric_name in self.integration_metrics:
                self.integration_metrics[metric_name] += count
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status"""
        return {
            "connection_status": "connected" if self.sf_client else "disconnected",
            "ai_agents_registered": {
                "lead_scoring": self.lead_scoring_agent is not None,
                "opportunity_analysis": self.opportunity_analyzer is not None,
                "customer_insights": self.customer_insights_agent is not None,
                "email_assistant": self.email_assistant is not None
            },
            "integration_metrics": self.integration_metrics,
            "last_updated": datetime.now().isoformat()
        }