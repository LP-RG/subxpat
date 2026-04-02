module abs_diff_i744_o372(a,b,r);
input [371:0] a,b;
output [371:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
