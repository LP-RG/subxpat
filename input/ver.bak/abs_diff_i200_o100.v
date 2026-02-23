module abs_diff_i200_o100(a,b,r);
input [99:0] a,b;
output [99:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
