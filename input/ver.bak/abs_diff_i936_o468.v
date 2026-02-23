module abs_diff_i936_o468(a,b,r);
input [467:0] a,b;
output [467:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
