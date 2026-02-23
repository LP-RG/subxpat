module abs_diff_i652_o326(a,b,r);
input [325:0] a,b;
output [325:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
