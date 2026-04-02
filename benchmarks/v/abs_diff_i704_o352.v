module abs_diff_i704_o352(a,b,r);
input [351:0] a,b;
output [351:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
