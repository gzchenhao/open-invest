"""
AI Agent Direct Apply Integration Example
Demonstrates how to use the AI Agent Direct Apply hook for seamless policy applications
"""

import asyncio
import logging
from typing import Dict, Any, List

# Import the AI Agent Direct Apply hook
from client.api.protocol_client import ProtocolClient, ClientType
from client.hooks.ai_agent_direct_apply import AIAgentDirectApply, ApplyResult, ApplicationStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvestmentPromotionManager:
    """Investment promotion manager using AI Agent Direct Apply"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = ProtocolClient(server_url, ClientType.GOV)
        self.direct_apply = AIAgentDirectApply(self.client)
    
    async def browse_and_apply_workflow(self, project_id: str, policy_id: str) -> ApplyResult:
        """
        Complete workflow: browse policies and apply directly
        
        Args:
            project_id: ID of the project to apply
            policy_id: ID of the target policy
            
        Returns:
            ApplyResult: Application result
        """
        logger.info(f"Starting browse and apply workflow for {project_id} -> {policy_id}")
        
        try:
            # Step 1: Browse available policies (simulated)
            available_policies = await self._browse_available_policies(project_id)
            logger.info(f"Found {len(available_policies)} suitable policies")
            
            # Step 2: Select the best matching policy
            selected_policy = await self._select_best_policy(project_id, available_policies)
            logger.info(f"Selected policy: {selected_policy['title']}")
            
            # Step 3: Trigger direct application
            application_result = await self.direct_apply.trigger_direct_apply(
                project_id, selected_policy['policy_id']
            )
            
            logger.info(f"Application submitted: {application_result.application_id}")
            return application_result
            
        except Exception as e:
            logger.error(f"Error in browse and apply workflow: {str(e)}")
            raise
    
    async def batch_application_campaign(self, project_ids: List[str], policy_id: str) -> List[ApplyResult]:
        """
        Submit multiple applications to the same policy
        
        Args:
            project_ids: List of project IDs to apply
            policy_id: Target policy ID
            
        Returns:
            List of ApplyResult objects
        """
        logger.info(f"Starting batch application campaign for {len(project_ids)} projects")
        
        results = []
        
        for project_id in project_ids:
            try:
                result = await self.direct_apply.trigger_direct_apply(project_id, policy_id)
                results.append(result)
                logger.info(f"Batch application {len(results)}/{len(project_ids)} completed")
                
            except Exception as e:
                logger.error(f"Error in batch application for {project_id}: {str(e)}")
                results.append(None)
        
        logger.info(f"Batch campaign completed: {len([r for r in results if r])}/{len(project_ids)} successful")
        return results
    
    async def cross_region_application(self, project_id: str, target_regions: List[str]) -> Dict[str, ApplyResult]:
        """
        Apply the same project to multiple regions
        
        Args:
            project_id: ID of the project to apply
            target_regions: List of target regions (e.g., ['shanghai', 'silicon_valley'])
            
        Returns:
            Dict mapping regions to application results
        """
        logger.info(f"Starting cross-region application for {project_id} to {len(target_regions)} regions")
        
        results = {}
        
        for region in target_regions:
            try:
                # Construct policy ID for the region
                policy_id = f"{region}-tech-hub-2024"
                
                result = await self.direct_apply.trigger_direct_apply(project_id, policy_id)
                results[region] = result
                
                logger.info(f"Cross-region application for {region}: {result.application_id}")
                
                # Add delay to avoid overwhelming the system
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in cross-region application for {region}: {str(e)}")
                results[region] = None
        
        return results
    
    async def track_application_progress(self, application_id: str) -> Dict[str, Any]:
        """
        Track application progress
        
        Args:
            application_id: ID of the application to track
            
        Returns:
            Dict containing application progress information
        """
        try:
            # Simulate progress tracking
            progress_info = {
                "application_id": application_id,
                "current_status": "under_review",
                "progress_percentage": 65,
                "estimated_completion": "2024-03-15",
                "contact_officer": "Dr. Sarah Chen",
                "recent_updates": [
                    "Initial screening completed",
                    "Technical evaluation in progress",
                    "Financial verification scheduled"
                ],
                "next_milestone": "Technical evaluation completion"
            }
            
            return progress_info
            
        except Exception as e:
            logger.error(f"Error tracking application progress: {str(e)}")
            return {"error": str(e)}
    
    async def _browse_available_policies(self, project_id: str) -> List[Dict[str, Any]]:
        """Browse available policies for a project"""
        # In real implementation, this would query the policy database
        return [
            {
                "policy_id": "shanghai-quantum-hub-2024",
                "title": "Shanghai Quantum Computing Hub Incentive",
                "location": "Shanghai, China",
                "industry_focus": ["quantum_computing", "ai"],
                "match_score": 0.85,
                "incentives": ["Tax credit", "Infrastructure grant", "Training support"],
                "deadline": "2024-12-31"
            },
            {
                "policy_id": "silicon_valley-quantum-2024",
                "title": "Silicon Valley Quantum Technology Program",
                "location": "California, USA",
                "industry_focus": ["quantum_computing", "ai"],
                "match_score": 0.92,
                "incentives": ["R&D tax credit", "Infrastructure grant", "Visa support"],
                "deadline": "2024-11-30"
            },
            {
                "policy_id": "singapore-ai-2024",
                "title": "Singapore AI Innovation Grant",
                "location": "Singapore",
                "industry_focus": ["ai", "machine_learning"],
                "match_score": 0.78,
                "incentives": ["Cash grant", "Tax incentive", "Market access"],
                "deadline": "2024-10-31"
            }
        ]
    
    async def _select_best_policy(self, project_id: str, available_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best matching policy"""
        # Sort by match score
        sorted_policies = sorted(available_policies, key=lambda x: x['match_score'], reverse=True)
        return sorted_policies[0]

async def main():
    """Main example usage"""
    
    # Initialize the investment promotion manager
    manager = InvestmentPromotionManager()
    
    # Example 1: Single application
    print("=== Example 1: Single Application ===")
    project_id = "quantum-encryption-startup-2024"
    policy_id = "shanghai-quantum-hub-2024"
    
    result = await manager.browse_and_apply_workflow(project_id, policy_id)
    print(f"Application Result: {result.application_id}")
    print(f"Status: {result.status}")
    print(f"Match Score: {result.match_score}")
    print(f"Next Steps: {result.next_steps}")
    
    # Example 2: Batch application
    print("\n=== Example 2: Batch Application ===")
    project_ids = [
        "quantum-encryption-startup-2024",
        "ai-robotics-company-2024",
        "biotech-innovation-lab-2024"
    ]
    policy_id = "shanghai-quantum-hub-2024"
    
    batch_results = await manager.batch_application_campaign(project_ids, policy_id)
    print(f"Batch Application Results: {len(batch_results)} applications submitted")
    
    # Example 3: Cross-region application
    print("\n=== Example 3: Cross-Region Application ===")
    project_id = "quantum-encryption-startup-2024"
    target_regions = ["shanghai", "silicon_valley", "singapore"]
    
    cross_region_results = await manager.cross_region_application(project_id, target_regions)
    print(f"Cross-Region Results: {len(cross_region_results)} regions applied")
    
    # Example 4: Application tracking
    print("\n=== Example 4: Application Tracking ===")
    if result:
        progress = await manager.track_application_progress(result.application_id)
        print(f"Application Progress: {progress['current_status']}")
        print(f"Progress Percentage: {progress['progress_percentage']}%")
        print(f"Contact Officer: {progress['contact_officer']}")

if __name__ == "__main__":
    asyncio.run(main())