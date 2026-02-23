module abs_diff_i148_o74(a,b,r);
input [73:0] a,b;
output [73:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
