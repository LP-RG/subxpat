module abs_diff_i832_o416(a,b,r);
input [415:0] a,b;
output [415:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
