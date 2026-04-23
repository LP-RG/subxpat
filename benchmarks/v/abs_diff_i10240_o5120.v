module abs_diff_i10240_o5120(a,b,r);
input [5119:0] a,b;
output [5119:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
