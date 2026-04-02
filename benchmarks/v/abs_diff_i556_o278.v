module abs_diff_i556_o278(a,b,r);
input [277:0] a,b;
output [277:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
