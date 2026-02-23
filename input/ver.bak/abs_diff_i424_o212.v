module abs_diff_i424_o212(a,b,r);
input [211:0] a,b;
output [211:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
