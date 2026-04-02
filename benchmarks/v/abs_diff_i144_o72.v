module abs_diff_i144_o72(a,b,r);
input [71:0] a,b;
output [71:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
